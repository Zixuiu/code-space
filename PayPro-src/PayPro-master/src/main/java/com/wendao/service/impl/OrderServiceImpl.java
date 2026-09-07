package com.wendao.service.impl;

import cn.hutool.http.HttpUtil;
import com.wendao.config.PayProConfig;
import com.wendao.entity.Order;
import com.wendao.exception.ApiException;
import com.wendao.mapper.OrderMapper;
import com.wendao.service.ProductService;
import com.wendao.enums.OrderStatesEnum;
import com.wendao.model.req.GetOrderListReq;
import com.wendao.model.req.OpenApiOrderReq;
import com.wendao.model.resp.AddOrderResp;
import com.wendao.model.resp.CountResp;
import com.wendao.model.resp.OpenApiOrderResp;
import com.wendao.service.OrderService;
import cn.hutool.core.date.DateUtil;
import cn.hutool.core.lang.Snowflake;
import com.wendao.entity.Product;
import com.wendao.model.ResponseVO;
import com.wendao.common.utils.*;
import com.wendao.model.req.OrderReq;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.wendao.utils.OpenApiSignUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.servlet.http.HttpServletRequest;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;
import java.math.BigDecimal;
import java.util.*;
import java.util.concurrent.TimeUnit;

/**
 */
@Service
public class OrderServiceImpl implements OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderServiceImpl.class);

    @Autowired
    private OrderMapper orderMapper;

    @Autowired
    StringRedisTemplate redisTemplate;

    @Autowired
    OrderService thisService;

    @Autowired
    PayProConfig payProConfig;

    @Autowired
    private EmailUtils emailUtils;

    @Autowired
    ProductService productService;

    @Autowired
    private SupabaseVipService supabaseVipService;

    @Autowired
    Snowflake snowflake;

    /**
     * 动态获取当前访问域名(协议+主机)，免疫 cpolar/花生壳 等隧道域名漂移。
     * 优先取反向代理透传的 X-Forwarded-* 头；无请求上下文(如异步线程)时回退配置 site。
     */
    private String currentSite() {
        try {
            ServletRequestAttributes attrs = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
            if (attrs != null) {
                HttpServletRequest req = attrs.getRequest();
                String proto = req.getHeader("X-Forwarded-Proto");
                if (proto == null || proto.trim().isEmpty()) {
                    proto = req.getScheme();
                }
                String host = req.getHeader("X-Forwarded-Host");
                if (host == null || host.trim().isEmpty()) {
                    host = req.getServerName();
                }
                if (host != null && !host.trim().isEmpty()) {
                    host = host.trim();
                    StringBuilder sb = new StringBuilder(proto.trim()).append("://").append(host);
                    int port = req.getServerPort();
                    if (!host.contains(":") && port != 80 && port != 443 && isLocalOrIp(host)) {
                        sb.append(":").append(port);
                    }
                    return sb.toString();
                }
            }
        } catch (Exception e) {
            log.warn("动态获取访问域名失败，回退使用配置 site: {}", e.getMessage());
        }
        return payProConfig.getSite();
    }

    private static boolean isLocalOrIp(String h) {
        if (h == null) return false;
        if ("localhost".equals(h) || h.endsWith(".localhost")) return true;
        return h.matches("^\\d{1,3}(\\.\\d{1,3}){3}$");
    }

    @Autowired
    OpenApiSignUtil openApiSignUtil;

    @Autowired
    private ResourceLoader resourceLoader;

    @Override
    public Order getOrderById(String id) {
        Order byId = orderMapper.selectById(id);
        byId.setTime(StringUtils.getTimeStamp(byId.getCreateTime()));
        return byId;
    }

    @Override
    public int addOrder(Order pay) {
        pay.setId(UUID.randomUUID().toString().replace("-", ""));
        pay.setCreateTime(new Date());
        pay.setState(OrderStatesEnum.WAIT_PAY.getState());
        // 如果未设置匹配模式，默认为备注模式
        if (pay.getMatchMode() == null) {
            pay.setMatchMode("REMARK");
        }
        if (pay.getActualAmount() == null) {
            pay.setActualAmount(pay.getMoney());
        }
        orderMapper.insert(pay);
        return 1;
    }

    @Override
    public int updateOrder(Order pay) {
        pay.setUpdateTime(new Date());
        orderMapper.updateById(pay);
        return 1;
    }

    @Override
    public int changeOrderState(String id, Integer state) {

        Order pay = getOrderById(id);
        pay.setState(state);
        pay.setUpdateTime(new Date());
        orderMapper.updateById(pay);
        return 1;
    }

    @Override
    public int delOrder(String id) {
        orderMapper.deleteById(id);
        return 1;
    }

    @Override
    public CountResp statistic(Integer type, String start, String end) {

        CountResp count = new CountResp();
        if (type == -1) {
            // 总
            count.setAmount(orderMapper.countAllMoney());
            count.setWeixin(orderMapper.countAllMoneyByType("Wechat"));
            count.setAlipay(orderMapper.countAllMoneyByType("Alipay"));
            return count;
        }
        Date startDate = null, endDate = null;
        if (type == 0) {
            // 今天
            startDate = DateUtils.getDayBegin();
            endDate = DateUtils.getDayEnd();
        }
        if (type == 6) {
            // 昨天
            startDate = DateUtils.getBeginDayOfYesterday();
            endDate = DateUtils.getEndDayOfYesterDay();
        } else if (type == 1) {
            // 本周
            startDate = DateUtils.getBeginDayOfWeek();
            endDate = DateUtils.getEndDayOfWeek();
        } else if (type == 2) {
            // 本月
            startDate = DateUtils.getBeginDayOfMonth();
            endDate = DateUtils.getEndDayOfMonth();
        } else if (type == 3) {
            // 本年
            startDate = DateUtils.getBeginDayOfYear();
            endDate = DateUtils.getEndDayOfYear();
        } else if (type == 4) {
            // 上周
            startDate = DateUtils.getBeginDayOfLastWeek();
            endDate = DateUtils.getEndDayOfLastWeek();
        } else if (type == 5) {
            // 上个月
            startDate = DateUtils.getBeginDayOfLastMonth();
            endDate = DateUtils.getEndDayOfLastMonth();
        } else if (type == -2) {
            // 自定义
            startDate = DateUtils.parseStartDate(start);
            endDate = DateUtils.parseEndDate(end);
        }
        count.setAmount(orderMapper.countMoney(startDate, endDate));
        count.setWeixin(orderMapper.countMoneyByType("Wechat", startDate, endDate));
        count.setAlipay(orderMapper.countMoneyByType("Alipay", startDate, endDate));
        return count;
    }

    @Override
    @Transactional
    public ResponseVO<AddOrderResp> addOrder(OrderReq req, HttpServletRequest request) {

        if(StringUtils.isBlank(String.valueOf(req.getMoney()))){
            return ResponseVO.errorResponse("请填写完整信息和正确金额");
        }

        String ip = IpInfoUtils.getIpAddr(request);

        Order entity = new Order();
        BeanUtils.copyProperties(req, entity);

        // --- 减额匹配逻辑 ---
        PayProConfig.Decrement decrementConfig = payProConfig.getDecrement();
        boolean isCustomAmount = req.getCustom() != null && req.getCustom();
        boolean isLocalQr = payProConfig.getUseLocalQrCode(req.getPayType());
        boolean useDecrement = decrementConfig.isEnabled()
                && !isCustomAmount
                && isLocalQr
                && !"wechat_zs".equals(req.getPayType());

        String matchMode = "REMARK";
        BigDecimal actualAmount = req.getMoney();
        Integer decrementIndex = null;
        boolean fallbackToRemark = false;

        // 修复并发同槽位竞争：锁必须覆盖「分配槽位 + 落库」整个临界区，
        // 否则锁释放后、INSERT 前，另一请求会读到同一空闲槽位，导致两个订单金额重复。
        String lockKey = null;
        Boolean locked = Boolean.FALSE;
        if (useDecrement) {
            lockKey = getDecrementLockKey(
                    req.getPayType(), String.format("%.2f", req.getMoney()));
            int retries = 3;
            while (retries > 0) {
                locked = redisTemplate.opsForValue()
                        .setIfAbsent(lockKey, "1", 5, TimeUnit.SECONDS);
                if (Boolean.TRUE.equals(locked)) {
                    break;
                }
                try { Thread.sleep(100); } catch (InterruptedException e) { break; }
                retries--;
            }
        }

        try {
            if (useDecrement) {
                DecrementSlotResult slotResult = tryAllocateDecrementSlot(
                        req.getPayType(), req.getMoney(), decrementConfig);

                if (!slotResult.isFallbackToRemark()) {
                    matchMode = "DECREMENT";
                    actualAmount = slotResult.getActualAmount();
                    decrementIndex = slotResult.getSlotIndex();
                } else {
                    matchMode = "REMARK";
                    actualAmount = slotResult.getActualAmount(); // base + step
                    fallbackToRemark = true;
                }
            }

            entity.setMatchMode(matchMode);
            entity.setActualAmount(actualAmount);
            entity.setDecrementIndex(decrementIndex);
            // --- 减额匹配逻辑结束 ---

            if (!isCustomAmount) {
                int i = new Random().nextInt(payProConfig.getQrCodeNum()) + 1;
                entity.setPayQrNum(i);
            } else {
                entity.setPayQrNum(1);
            }

            // 减额模式(非回退)不需要备注, 其他模式需要生成payNum
            if ("DECREMENT".equals(matchMode) && !fallbackToRemark) {
                entity.setPayNum(null);
            } else {
                entity.setPayNum(StringUtils.getRandomNum());
            }
            // INSERT 必须放在锁内，确保槽位占用对并发请求立即可见
            thisService.addOrder(entity);
        } catch (Exception e) {
            log.error(e.toString());
            return ResponseVO.errorResponse("添加捐赠支付订单失败");
        } finally {
            if (Boolean.TRUE.equals(locked) && lockKey != null) {
                redisTemplate.delete(lockKey);
            }
        }
        //记录缓存
        redisTemplate.opsForValue().set(ip, "added", payProConfig.getRateLimit().getIpExpire(), TimeUnit.MINUTES);

        //给管理员发送审核邮件
        String tokenAdmin = UUID.randomUUID().toString();
        redisTemplate.opsForValue().set(entity.getId(), tokenAdmin, payProConfig.getToken().getExpire(), TimeUnit.DAYS);
        entity = getAdminUrl(entity, entity.getId(), tokenAdmin, payProConfig.getToken().getValue());
        emailUtils.sendTemplateMail(payProConfig.getEmail().getSender(), payProConfig.getEmail().getReceiver(), "【" + payProConfig.getTitle() + "】待审核处理", "payment-review", entity);

        AddOrderResp addPayResp = new AddOrderResp();
        addPayResp.setId(entity.getId());
        addPayResp.setPayNum(entity.getPayNum());
        addPayResp.setPayType(entity.getPayType());
        addPayResp.setMoney(entity.getMoney());
        addPayResp.setPayQrNum(entity.getPayQrNum());
        addPayResp.setCustom(isCustomAmount || fallbackToRemark);
        addPayResp.setMatchMode(matchMode);
        addPayResp.setActualAmount(actualAmount);
        addPayResp.setFallbackToRemark(fallbackToRemark);
        return ResponseVO.successResponse(addPayResp);
    }

    /**
     * 处理充值业务,直接调用游戏的接口。订单状态在游戏的地方修改
     */
    @Override
    @Transactional
    public int pass(String id) {
        //Pay pay = thisService.changePayState(id, 1);
        Order pay = orderMapper.selectById(id);
        if ("PRODUCT".equals(pay.getOrderSource()) && pay.getProductId() != null) {
            Product product = productService.getProductById(pay.getProductId() != null ? pay.getProductId().intValue() : null);
            if (product != null && "CODE".equals(product.getType())) {
                // 自动发码：从码池文件取一个激活码发给买家（池空则邮件回退为客服人工发放文案）
                String licenseCode = takeLicenseCode(product.getId());
                pay.setLicenseCode(licenseCode);
                // 邮件发送失败不应阻断订单成功与发码（SMTP 未配置/临时故障时仍可手动补发）
                try {
                    emailUtils.sendTemplateMail(payProConfig.getEmail().getSender(), pay.getEmail(), "【" + payProConfig.getTitle() + "】支付成功通知（附激活码）",
                            "order-success", pay);
                } catch (Exception mailEx) {
                    log.error("激活码邮件发送失败（订单仍标记成功，可手动补发）: {}", mailEx.toString());
                }
                pay.setState(OrderStatesEnum.SUCCESS_PAY.getState());
                orderMapper.updateById(pay);
            }
        } else if ("OPENAPI".equals(pay.getOrderSource())) {
            callbackFaka(pay.getNotifyUrl(),pay.getId(),pay.getMoney(),pay.getPayNum());
            pay.setState(OrderStatesEnum.SUCCESS_PAY.getState());
            orderMapper.updateById(pay);
        } else {
            // 普通充值订单（orderSource 为空/OTHER）：审核通过即置为支付成功，供前端轮询感知
            pay.setState(OrderStatesEnum.SUCCESS_PAY.getState());
            pay.setUpdateTime(new Date());
            orderMapper.updateById(pay);
        }
        // 审核通过后尝试按订单邮箱自动开通 VIP（按 9.9 元 = 1 个月换算），并邮件通知到该邮箱
        try {
            if (pay.getEmail() != null && !pay.getEmail().trim().isEmpty()) {
                int months = pay.getMoney() != null
                        ? Math.max(1, pay.getMoney().divide(new BigDecimal("9.9"), 0, java.math.RoundingMode.DOWN).intValue())
                        : 1;
                String vipResult = supabaseVipService.activateByEmail(pay.getEmail(), months);
                log.info("订单 {} 审核通过，自动开通VIP(email={}, months={}) -> {}", id, pay.getEmail(), months, vipResult);
                // 开通成功(结果含"已开通至")才发通知邮件；失败/未找到用户不发误导邮件
                if (vipResult != null && vipResult.contains("已开通")) {
                    try {
                        pay.setNotice(vipResult);
                        emailUtils.sendTemplateMail(payProConfig.getEmail().getSender(), pay.getEmail(),
                                "【" + payProConfig.getTitle() + "】会员已开通通知", "order-vip", pay);
                    } catch (Exception mailEx) {
                        log.error("会员开通通知邮件发送失败（不影响开通）: {}", mailEx.toString());
                    }
                }
            }
        } catch (Exception vipEx) {
            // 不影响订单成功状态，仅记录
            log.error("自动开通VIP异常（订单已标记成功，可手动补开）: {}", vipEx.toString());
        }
        return 1;
    }

    /**
     * 从码池文件取一个激活码（首个非空行），并从池中移除（重写文件）。
     * 码池路径：config/cards/product-{productId}.txt（每行一个码，# 开头为注释）。
     * 取出的码追加记录到 config/cards/used-codes.log 便于审计与补发。
     * 池为空或文件缺失时返回 null（邮件回退为客服人工发放文案）。
     */
    private String takeLicenseCode(Integer productId) {
        if (productId == null) {
            return null;
        }
        java.io.File pool = new java.io.File("config/cards/product-" + productId + ".txt");
        try {
            if (!pool.isFile()) {
                log.warn("码池文件不存在: {}", pool.getAbsolutePath());
                return null;
            }
            java.util.List<String> lines = java.nio.file.Files.readAllLines(pool.toPath(), java.nio.charset.StandardCharsets.UTF_8);
            String code = null;
            java.util.List<String> rest = new java.util.ArrayList<>();
            for (String l : lines) {
                String t = (l == null) ? "" : l.trim();
                if (code == null && !t.isEmpty() && !t.startsWith("#")) {
                    code = t;
                    continue;
                }
                rest.add(l);
            }
            if (code == null) {
                log.warn("码池已空: {}", pool.getAbsolutePath());
                return null;
            }
            java.nio.file.Files.write(pool.toPath(), rest, java.nio.charset.StandardCharsets.UTF_8);
            java.io.File usedLog = new java.io.File(pool.getParentFile(), "used-codes.log");
            java.nio.file.Files.write(usedLog.toPath(),
                    (System.currentTimeMillis() + "|" + code + System.lineSeparator()).getBytes(java.nio.charset.StandardCharsets.UTF_8),
                    java.nio.file.StandardOpenOption.CREATE, java.nio.file.StandardOpenOption.APPEND);
            log.info("已从码池发放激活码: {}", code);
            return code;
        } catch (Exception e) {
            log.error("读取码池失败: " + e.toString());
            return null;
        }
    }

    @Override
    public IPage<Order> list(GetOrderListReq req) {

        LambdaQueryWrapper<Order> wrapper = Wrappers.lambdaQuery();
        wrapper.in(Order::getState, req.getStates());
        if (StringUtils.isNotBlank(req.getOrderBy())) {

            if (req.getOrder().equals("createTime")) {
                if (req.getOrder().equals("desc")) {
                    wrapper.orderByDesc(Order::getCreateTime);
                } else {
                    wrapper.orderByAsc(Order::getCreateTime);
                }
            }

            if (req.getOrder().equals("money")) {
                if (req.getOrder().equals("desc")) {
                    wrapper.orderByDesc(Order::getMoney);
                } else {
                    wrapper.orderByAsc(Order::getMoney);
                }
            }
        }

        if (StringUtils.isNotBlank(req.getKeyword())) {
            //字符串类型的处理，统一全部like查询
            wrapper.like(Order::getEmail, req.getKeyword());
            wrapper.or().like(Order::getNickName, req.getKeyword());
        }
        Page<Order> page = new Page<>(req.getPageIndex(), req.getPageSize());
        Page<Order> payPage = orderMapper.selectPage(page, wrapper);

        for (Order record : payPage.getRecords()) {
            // 屏蔽隐私数据
            record.setId("");
            record.setEmail("");
            record.setPayNum(null);
            record.setMobile(null);
            record.setCustom(null);
            record.setDevice(null);
        }
        return payPage;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public OpenApiOrderResp createOpenApiOrder(OpenApiOrderReq req) {
        if (!openApiSignUtil.verifyTimestamp(req.getTimestamp())) {
            throw new ApiException(ApiException.ErrorCode.TIMESTAMP_ERROR, "请求时间戳无效或已过期");
        }

        if (!openApiSignUtil.verifySign(req)) {
            throw new ApiException(ApiException.ErrorCode.SIGN_ERROR, "签名验证失败");
        }

        if (req.getAmount() == null || req.getAmount().compareTo(new BigDecimal("0")) <= 0) {
            throw new ApiException(ApiException.ErrorCode.AMOUNT_ERROR, "金额必须大于0");
        }

        if (req.getAmount().compareTo(new BigDecimal("100000")) > 0) {
            throw new ApiException(ApiException.ErrorCode.AMOUNT_ERROR, "金额超出限制，单笔订单不能超过100000元");
        }

        Order existingOrder = orderMapper.selectById(req.getOrderNo());
        if (existingOrder != null) {
            throw new ApiException(ApiException.ErrorCode.DUPLICATE_ORDER, "订单号已存在");
        }

        Order order = new Order();
        order.setId(req.getOrderNo());
        order.setMoney(req.getAmount());
        order.setPayType(req.getPayType());
        order.setNickName(req.getNickName());
        order.setEmail(req.getEmail());
        order.setNotifyUrl(req.getNotifyUrl());
        order.setUserId(req.getUserId());
        order.setProductId(req.getProductId());
        order.setOrderSource("OPENAPI");
        order.setState(OrderStatesEnum.WAIT_PAY.getState());
        order.setCreateTime(new Date());


        // --- 减额匹配逻辑(OpenAPI) ---
        PayProConfig.Decrement decrementConfig = payProConfig.getDecrement();
        boolean isCustomAmount = req.getCustom() != null && req.getCustom();
        boolean isLocalQr = payProConfig.getUseLocalQrCode(req.getPayType());
        boolean useDecrement = decrementConfig.isEnabled()
                && !isCustomAmount
                && isLocalQr
                && !"wechat_zs".equals(req.getPayType());

        String matchMode = "REMARK";
        BigDecimal actualAmount = req.getAmount();
        Integer decrementIndex = null;
        boolean fallbackToRemark = false;

        // 修复并发同槽位竞争：锁须覆盖「分配槽位 + 落库」，INSERT 在锁释放前完成，
        // 否则并发下单会读到同一空闲槽位、分到相同减额金额。
        String lockKey = null;
        Boolean locked = Boolean.FALSE;
        if (useDecrement) {
            lockKey = getDecrementLockKey(
                    req.getPayType(), String.format("%.2f", req.getAmount()));
            int retries = 3;
            while (retries > 0) {
                locked = redisTemplate.opsForValue()
                        .setIfAbsent(lockKey, "1", 5, TimeUnit.SECONDS);
                if (Boolean.TRUE.equals(locked)) { break; }
                try { Thread.sleep(100); } catch (InterruptedException e) { break; }
                retries--;
            }
        }

        String qrUrl = "";
        String returnUrl = "";
        try {
            if (useDecrement) {
                DecrementSlotResult slotResult = tryAllocateDecrementSlot(
                        req.getPayType(), req.getAmount(), decrementConfig);

                if (!slotResult.isFallbackToRemark()) {
                    matchMode = "DECREMENT";
                    actualAmount = slotResult.getActualAmount();
                    decrementIndex = slotResult.getSlotIndex();
                } else {
                    matchMode = "REMARK";
                    actualAmount = slotResult.getActualAmount();
                    fallbackToRemark = true;
                }
            }

            order.setMatchMode(matchMode);
            order.setActualAmount(actualAmount);
            order.setDecrementIndex(decrementIndex);

            // 减额模式(非回退)不需要备注
            if ("DECREMENT".equals(matchMode) && !fallbackToRemark) {
                order.setPayNum(null);
            } else {
                order.setPayNum(StringUtils.getRandomNum());
            }
            // --- 减额匹配逻辑结束 ---

            int i = new Random().nextInt(payProConfig.getQrCodeNum()) + 1;
            order.setPayQrNum(i);

            // 格式化金额为两位小数
            String formattedAmount = String.format("%.2f", req.getAmount());
            String actualFormattedAmount = String.format("%.2f", actualAmount);

            // 减额模式或回退模式: 放在基础金额目录下; 普通备注模式: 检查金额QR是否存在
            if ("DECREMENT".equals(matchMode) && !fallbackToRemark) {
                if (actualAmount.compareTo(req.getAmount()) == 0) {
                    qrUrl = currentSite() + "/assets/qr/" + req.getPayType() + "/" +
                            formattedAmount + "/" + i + ".png";
                } else {
                    qrUrl = currentSite() + "/assets/qr/" + req.getPayType() + "/" +
                            formattedAmount + "/" + actualFormattedAmount + "/" + i + ".png";
                }
                req.setCustom(false);
            } else if (fallbackToRemark) {
                // 回退模式: 金额+0.01区分，如5.01放在5.00目录下
                qrUrl = currentSite() + "/assets/qr/" + req.getPayType() + "/" +
                        formattedAmount + "/" + actualFormattedAmount + "/" + i + ".png";
                req.setCustom(true);
            } else {
                boolean b = checkQrFileExists(req.getPayType(), req.getAmount(), i);
                if (!b) {
                    qrUrl = currentSite() + "/assets/qr/" + req.getPayType() + "/" +
                            formattedAmount + "/" + i + ".png";
                    req.setCustom(false);
                } else {
                    qrUrl = currentSite() + "/assets/qr/" + req.getPayType() + "/" + "custom.png";
                    req.setCustom(true);
                }
            }

            // 获取支付类型配置
            Boolean useLocalQrCodeConfig = payProConfig.getUseLocalQrCode(req.getPayType());
            returnUrl = currentSite() + "/payment.html?" +
                    "orderId=" + req.getOrderNo() +
                    "&money=" + req.getAmount() +
                    "&payType=" + req.getPayType() +
                    "&payNum=" + (order.getPayNum() != null ? order.getPayNum() : "") +
                    "&customerQr=" + (req.getCustom() || fallbackToRemark) +
                    "&picName=" + formattedAmount +
                    "&qrCode=" + "undefined" +
                    "&payQrNum=" + i +
                    "&useLocalQrCode=" + useLocalQrCodeConfig +
                    "&matchMode=" + matchMode +
                    "&actualAmount=" + actualFormattedAmount +
                    "&fallbackToRemark=" + fallbackToRemark;

            // 落库必须发生在锁内，确保槽位占用对并发可见
            orderMapper.insert(order);
        } catch (Exception e) {
            log.error("创建OpenApi订单失败: {}", e.getMessage(), e);
            throw new ApiException(ApiException.ErrorCode.SYSTEM_ERROR, "创建订单失败");
        } finally {
            if (Boolean.TRUE.equals(locked) && lockKey != null) {
                redisTemplate.delete(lockKey);
            }
        }

        String tokenAdmin = UUID.randomUUID().toString();
        redisTemplate.opsForValue().set(order.getId(), tokenAdmin, payProConfig.getToken().getExpire(), TimeUnit.DAYS);
        order = getAdminUrl(order, order.getId(), tokenAdmin, payProConfig.getToken().getValue());
        emailUtils.sendTemplateMail(payProConfig.getEmail().getSender(), payProConfig.getEmail().getReceiver(), "【OPENAPI】待审核处理", "payment-review", order);

        return OpenApiOrderResp.builder()
                .orderId(order.getId())
                .orderNo(req.getOrderNo())
                .amount(req.getAmount())
                .payType(req.getPayType())
                .payNum(order.getPayNum())
                .state(order.getState())
                .message("订单创建成功")
                .qrCodeUrl(qrUrl)
                .returnUrl(returnUrl)
                .timestamp(System.currentTimeMillis())
                .matchMode(matchMode)
                .actualAmount(actualAmount)
                .fallbackToRemark(fallbackToRemark)
                .build();
    }

    /**
     * 检查指定支付类型和金额的二维码文件是否存在
     *
     * @param payType 支付类型，如 "wechat"、"alipay"，需与文件夹名称匹配
     * @param amount  金额，将格式化为两位小数作为文件夹名
     * @param qrNum   二维码编号，用于构建文件名
     * @return 文件存在返回 true，否则返回 false
     */
    private boolean checkQrFileExists(String payType, BigDecimal amount, int qrNum) {
        // 格式化金额为两位小数，与文件夹名称一致
        String amountStr = String.format("%.2f", amount);
        String relativePath = payType.toLowerCase() + "/" + amountStr + "/" + qrNum + ".png";

        // 优先检查外部目录
        String qrDir = payProConfig.getQrDir();
        if (org.springframework.util.StringUtils.hasText(qrDir)) {
            String externalPath = qrDir.endsWith("/") ? qrDir + relativePath : qrDir + "/" + relativePath;
            try {
                if (resourceLoader.getResource("file:" + externalPath).exists()) {
                    return true;
                }
            } catch (Exception e) {
                // ignore, try classpath fallback
            }
        }

        // classpath 回退（修复原 bug：static/qr -> static/assets/qr）
        String classpathPath = "classpath:static/assets/qr/" + relativePath;
        try {
            Resource resource = resourceLoader.getResource(classpathPath);
            return resource.exists();
        } catch (Exception e) {
            return false;
        }
    }


    /**
     * 拼接管理员链接
     */
    public Order getAdminUrl(Order pay, String id, String token, String myToken) {

        String pass = currentSite() + "/order/pass?id=" + id + "&token=" + token + "&myToken=" + myToken;
        pay.setPassUrl(pass);

        String back = currentSite() + "/order/back?id=" + id + "&token=" + token + "&myToken=" + myToken;
        pay.setBackUrl(back);

        String edit = currentSite() + "/order-edit?id=" + id + "&token=" + token;
        pay.setEditUrl(edit);

        String del = currentSite() + "/order-del?id=" + id + "&token=" + token;
        pay.setDelUrl(del);

        String close = currentSite() + "/order-close?id=" + id + "&token=" + token;
        pay.setCloseUrl(close);

        String statistic = currentSite() + "/statistic?myToken=" + myToken;
        pay.setStatistic(statistic);
        return pay;
    }

    public void callbackFaka(String notifyUrl, String orderNo, BigDecimal amount, String payNum) {
        Map<String, Object> params = new TreeMap<>();
        params.put("orderNo", orderNo);
        params.put("amount", amount);
        params.put("payNum", payNum);

        // 生成签名
        String sign = openApiSignUtil.generateSign(params);
        params.put("sign", sign);
        HttpUtil.post(notifyUrl, com.alibaba.fastjson2.JSONObject.toJSONString(params));
    }
    // ==================== 减额匹配相关方法 ====================

    /**
     * 减额匹配槽位分配结果
     */
    @lombok.Data
    private static class DecrementSlotResult {
        private boolean success;
        private boolean fallbackToRemark;
        private int slotIndex;
        private BigDecimal actualAmount;
    }

    /**
     * 尝试分配减额槽位
     * maxCount = 向下递减次数(不含基准价)
     * 例如 maxCount=2: 槽位0=5.00, 槽位1=4.99, 槽位2=4.98
     *
     * @param payType    支付类型
     * @param baseAmount 基础金额(原始订单金额)
     * @param config     减额配置
     * @return 槽位分配结果
     */
    private DecrementSlotResult tryAllocateDecrementSlot(
            String payType, BigDecimal baseAmount, PayProConfig.Decrement config) {

        BigDecimal step = config.getStep();
        int maxCount = config.getMaxCount();

        // 收集已占用的槽位索引
        Set<Integer> occupiedSlots = new HashSet<>();
        for (int i = 0; i <= maxCount; i++) {
            BigDecimal slotAmount = baseAmount.subtract(step.multiply(new BigDecimal(i)));
            // 实际金额必须 > 0
            if (slotAmount.compareTo(BigDecimal.ZERO) <= 0) {
                occupiedSlots.add(i);
                continue;
            }
            // 检查该金额的QR码文件是否存在(任意编号)
            if (!checkAnyQrFileExists(payType, baseAmount, slotAmount)) {
                log.warn("减额槽位{}金额{}的QR码文件不存在，跳过该槽位", i, String.format("%.2f", slotAmount));
                occupiedSlots.add(i);
                continue;
            }
            // 查询该金额下是否有活跃订单
            List<Order> activeOrders = orderMapper.selectList(
                    new LambdaQueryWrapper<Order>()
                            .eq(Order::getActualAmount, slotAmount)
                            .eq(Order::getMatchMode, "DECREMENT")
                            .in(Order::getState, 0, 4));
            if (activeOrders != null && !activeOrders.isEmpty()) {
                occupiedSlots.add(i);
            }
        }

        // 找第一个可用槽位
        for (int i = 0; i <= maxCount; i++) {
            if (!occupiedSlots.contains(i)) {
                BigDecimal actualAmount = baseAmount.subtract(step.multiply(new BigDecimal(i)));
                DecrementSlotResult result = new DecrementSlotResult();
                result.setSuccess(true);
                result.setSlotIndex(i);
                result.setActualAmount(actualAmount);
                result.setFallbackToRemark(false);
                return result;
            }
        }

        // 所有槽位被占用 -- 回退到备注模式
        DecrementSlotResult result = new DecrementSlotResult();
        result.setSuccess(true);
        result.setFallbackToRemark(true);
        // 回退金额 = 基础金额 + step，用不同金额区分
        result.setActualAmount(baseAmount.add(step));
        return result;
    }

    /**
     * 检查指定支付类型和金额下是否有任意QR码文件存在(使用正确的assets/qr路径)
     * 减额二维码放在基础金额目录下: {payType}/{baseAmount}/{amount}/{qrNum}.png
     * 槽位0(金额等于基础金额)保持原有路径: {payType}/{baseAmount}/{qrNum}.png
     */
    private boolean checkAnyQrFileExists(String payType, BigDecimal baseAmount, BigDecimal amount) {
        String baseAmountStr = String.format("%.2f", baseAmount);
        String amountStr = String.format("%.2f", amount);
        for (int i = 1; i <= payProConfig.getQrCodeNum(); i++) {
            String filePath;
            if (amount.compareTo(baseAmount) == 0) {
                // 槽位0: 基础金额目录下直接放二维码
                filePath = "classpath:static/assets/qr/" + payType.toLowerCase()
                        + "/" + baseAmountStr + "/" + i + ".png";
            } else {
                // 减额槽位: 放在基础金额目录下的子目录
                filePath = "classpath:static/assets/qr/" + payType.toLowerCase()
                        + "/" + baseAmountStr + "/" + amountStr + "/" + i + ".png";
            }
            try {
                Resource resource = resourceLoader.getResource(filePath);
                if (resource.exists()) {
                    return true;
                }
            } catch (Exception e) {
                // ignore, try next
            }
        }
        return false;
    }

    @Override
    public Order getByActualAmount(BigDecimal actualAmount, Date startTime, Date endTime) {
        return orderMapper.getDecrementOrderByAmount(actualAmount, startTime, endTime);
    }

    @Override
    public Set<Integer> getOccupiedDecrementSlots(String payType, BigDecimal baseAmount) {
        PayProConfig.Decrement config = payProConfig.getDecrement();
        if (config == null || !config.isEnabled()) {
            return Collections.emptySet();
        }
        Set<Integer> occupied = new HashSet<>();
        BigDecimal step = config.getStep();
        for (int i = 0; i <= config.getMaxCount(); i++) {
            BigDecimal slotAmount = baseAmount.subtract(step.multiply(new BigDecimal(i)));
            if (slotAmount.compareTo(BigDecimal.ZERO) <= 0) {
                continue;
            }
            List<Order> orders = orderMapper.selectList(
                    new LambdaQueryWrapper<Order>()
                            .eq(Order::getActualAmount, slotAmount)
                            .eq(Order::getMatchMode, "DECREMENT")
                            .in(Order::getState, 0, 4));
            if (orders != null && !orders.isEmpty()) {
                occupied.add(i);
            }
        }
        return occupied;
    }

    public static String getDecrementLockKey(String payType, String baseAmount) {
        return "pay:decrement_lock:" + payType + ":" + baseAmount;
    }

}
