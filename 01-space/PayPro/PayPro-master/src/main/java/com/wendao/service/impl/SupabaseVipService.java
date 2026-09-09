package com.wendao.service.impl;

import cn.hutool.http.HttpRequest;
import cn.hutool.http.HttpResponse;
import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.wendao.config.PayProConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Supabase 会员服务：支付订单审核通过后，用订单邮箱自动开通对应月数的 VIP。
 * 逻辑与 PC-Action 客户端 database_helper.manage_vip_license 保持一致：
 *   1) 按 email 查 users 表；
 *   2) 写/更新 licenses 表（已有未过期则叠加时长）；
 *   3) 同步更新 users.is_vip / vip_end_date。
 */
@Service
public class SupabaseVipService {

    private static final Logger log = LoggerFactory.getLogger(SupabaseVipService.class);

    /** Supabase 项目地址（REST 基准） */
    private static final String SUPABASE_URL = "https://loifmrvoignxlifizogv.supabase.co";
    /** anon key（只读/写权限由 RLS 控制，与客户端一致） */
    private static final String SUPABASE_KEY =
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvaWZtcnZvaWdueGxpZml6b2d2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA5NTA3ODksImV4cCI6MjA3NjUyNjc4OX0.EtuSOO6pms-kkHiR4g1lLU8As-J0mWR0WIO8TiwselQ";

    private static final String REST = "/rest/v1";
    private static final DateTimeFormatter DTF = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    public boolean isSupabaseConfigured() {
        return SUPABASE_URL != null && !SUPABASE_URL.isEmpty()
                && SUPABASE_KEY != null && !SUPABASE_KEY.isEmpty();
    }

    /**
     * 按邮箱为指定用户开通/续费 VIP。
     *
     * @param email  用户注册邮箱
     * @param months 月数
     * @return 结果描述；null 表示无需处理（邮箱为空/用户不存在）
     */
    public String activateByEmail(String email, int months) {
        if (email == null || email.trim().isEmpty()) {
            return "邮箱为空，跳过开通";
        }
        if (months <= 0) {
            return "月数无效，跳过开通";
        }
        if (!isSupabaseConfigured()) {
            return "Supabase 未配置";
        }
        try {
            JSONObject user = findUserByEmail(email.trim());
            if (user == null) {
                return "未找到邮箱对应的用户: " + email;
            }
            Object userId = user.get("id");
            if (userId == null) {
                return "用户缺少 id";
            }

            LocalDate newExpiry = LocalDate.now().plusDays((long) months * 30);

            // 1) licenses 表：已有未过期 license 则叠加时长，否则新建；返回最终到期日
            LocalDate finalExpiry = upsertLicense(String.valueOf(userId), newExpiry, months);
            if (finalExpiry == null) {
                return "写入许可证失败 (email=" + email + ")";
            }

            // 2) users 表同步（以叠加后的最终到期日为准，保证两表一致）
            Map<String, Object> patch = new HashMap<>();
            patch.put("is_vip", 1);
            patch.put("vip_end_date", finalExpiry.format(DTF));
            boolean opu = patchUser(String.valueOf(userId), patch);
            if (!opu) {
                return "会员状态同步失败 (email=" + email + ")";
            }

            return "会员已开通至 " + finalExpiry.format(DTF);
        } catch (Exception e) {
            log.error("Supabase 开通VIP失败: email={}, months={}, err={}", email, months, e.toString());
            return "开通VIP异常: " + e.getMessage();
        }
    }

    /**
     * 到期归零：把已过期(vip_end_date < 今天)且 is_vip=1 的用户批量置为 is_vip=0。
     * 客户端 entitlement 已按日期判定锁定，此方法作为数据库层双保险。
     * @return 处理的用户数量
     */
    public int expireOverdueUsers() {
        if (!isSupabaseConfigured()) {
            return 0;
        }
        try {
            String today = LocalDate.now().format(DTF);
            // 查出过期且仍标记为 vip 的用户
            HttpResponse q = HttpRequest.get(SUPABASE_URL + REST + "/users")
                    .header("apikey", SUPABASE_KEY)
                    .header("Authorization", "Bearer " + SUPABASE_KEY)
                    .header("Content-Type", "application/json")
                    .form("select", "id")
                    .form("is_vip", "eq.1")
                    .form("vip_end_date", "lt." + today)
                    .timeout(8000)
                    .execute();
            String qBody = q.body();
            q.close();
            JSONArray arr = JSONUtil.parseArray(qBody);
            if (arr == null || arr.isEmpty()) {
                return 0;
            }
            int count = 0;
            for (Object o : arr) {
                JSONObject u = (JSONObject) o;
                count += patchUser(String.valueOf(u.get("id")), java.util.Collections.singletonMap("is_vip", 0)) ? 1 : 0;
            }
            log.info("Supabase 到期归零处理用户数: {}", count);
            return count;
        } catch (Exception e) {
            log.error("Supabase 到期归零异常: {}", e.toString());
            return 0;
        }
    }

    private JSONObject findUserByEmail(String email) {
        // 邮箱是用户唯一标识，必须可靠命中。原 eq 为大小写敏感的精确匹配，
        // 注册/下单只要大小写或首尾空格不一致就会漏匹配（"未找到邮箱对应用户"）。
        // 改用大小写不敏感的 ilike 精确匹配，并转义 % _ \ 避免被当成 LIKE 通配符。
        String probe = email.trim().toLowerCase();
        String escaped = probe
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_");
        HttpResponse resp = HttpRequest.get(SUPABASE_URL + REST + "/users")
                .header("apikey", SUPABASE_KEY)
                .header("Authorization", "Bearer " + SUPABASE_KEY)
                .header("Content-Type", "application/json")
                .form("select", "*")
                .form("email", "ilike." + escaped)
                .timeout(8000)
                .execute();
        String body = resp.body();
        int status = resp.getStatus();
        resp.close();
        log.info("Supabase 查询用户 email={} -> {} {}", email, status, body);
        JSONArray arr = JSONUtil.parseArray(body);
        if (arr != null && !arr.isEmpty()) {
            return arr.getJSONObject(0);
        }
        log.warn("Supabase 未匹配到用户 email={}",
                email + " (原请求精确匹配被改为大小写不敏感，仍无一命中，需核对订单与实际注册邮箱)");
        return null;
    }

    private LocalDate upsertLicense(String userId, LocalDate newExpiry, int months) {
        // 查已有 license
        HttpResponse q = HttpRequest.get(SUPABASE_URL + REST + "/licenses")
                .header("apikey", SUPABASE_KEY)
                .header("Authorization", "Bearer " + SUPABASE_KEY)
                .header("Content-Type", "application/json")
                .form("select", "*")
                .form("user_id", "eq." + userId)
                .timeout(8000)
                .execute();
        String qBody = q.body();
        q.close();
        JSONArray arr = JSONUtil.parseArray(qBody);

        if (arr != null && !arr.isEmpty()) {
            JSONObject existing = arr.getJSONObject(0);
            Object id = existing.get("id");
            Object exp = existing.get("expiry_date");
            // 已有未过期 license 时叠加
            LocalDate base = LocalDate.now();
            if (exp != null) {
                try {
                    LocalDate ex = LocalDate.parse(String.valueOf(exp).substring(0, 10), DTF);
                    if (ex.isAfter(LocalDate.now())) {
                        base = ex;
                    }
                } catch (Exception ignore) {
                }
            }
            LocalDate target = base.plusDays((long) months * 30);
            JSONObject patch = new JSONObject();
            patch.set("expiry_date", target.format(DTF));
            HttpResponse up = HttpRequest.patch(SUPABASE_URL + REST + "/licenses?id=eq." + id)
                    .header("apikey", SUPABASE_KEY)
                    .header("Authorization", "Bearer " + SUPABASE_KEY)
                    .header("Content-Type", "application/json")
                    .body(patch.toString())
                    .timeout(8000)
                    .execute();
            int st = up.getStatus();
            String b = up.body();
            up.close();
            log.info("Supabase 更新 license id={} -> {} {}", id, st, b);
            return st >= 200 && st < 300 ? target : null;
        }

        // 新建 license
        JSONObject row = new JSONObject();
        // user_id 保持字符串传给 PostgREST，由其按列类型(uuid/bigint)自动转换；
        // 原 Integer.valueOf 在 user.id 为 UUID 时会抛 NumberFormatException 导致开通失败
        row.set("user_id", userId);
        row.set("license_key", "VIP-" + UUID.randomUUID().toString().replace("-", "").substring(0, 8).toUpperCase());
        row.set("product_name", "VIP会员");
        row.set("expiry_date", newExpiry.format(DTF));
        row.set("created_at", LocalDate.now().atStartOfDay().format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
        HttpResponse ins = HttpRequest.post(SUPABASE_URL + REST + "/licenses")
                .header("apikey", SUPABASE_KEY)
                .header("Authorization", "Bearer " + SUPABASE_KEY)
                .header("Content-Type", "application/json")
                .header("Prefer", "return=minimal")
                .body(row.toString())
                .timeout(8000)
                .execute();
        int st = ins.getStatus();
        String b = ins.body();
        ins.close();
        log.info("Supabase 新建 license -> {} {}", st, b);
        return st >= 200 && st < 300 ? newExpiry : null;
    }

    private boolean patchUser(String userId, Map<String, Object> updates) {
        JSONObject body = new JSONObject();
        updates.forEach(body::set);
        HttpResponse resp = HttpRequest.patch(SUPABASE_URL + REST + "/users?id=eq." + userId)
                .header("apikey", SUPABASE_KEY)
                .header("Authorization", "Bearer " + SUPABASE_KEY)
                .header("Content-Type", "application/json")
                .body(body.toString())
                .timeout(8000)
                .execute();
        int st = resp.getStatus();
        String b = resp.body();
        resp.close();
        log.info("Supabase 更新 users id={} -> {} {}", userId, st, b);
        return st >= 200 && st < 300;
    }
}