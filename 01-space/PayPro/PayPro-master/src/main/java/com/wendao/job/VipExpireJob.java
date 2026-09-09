package com.wendao.job;

import com.wendao.service.impl.SupabaseVipService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 会员到期归零定时任务：每天执行一次，把已过期的会员在数据库中置为非 VIP。
 */
@Component
public class VipExpireJob {

    private static final Logger log = LoggerFactory.getLogger(VipExpireJob.class);

    @Autowired
    private SupabaseVipService supabaseVipService;

    /** 每天 01:10 执行到期清理 */
    @Scheduled(cron = "0 10 1 * * ?")
    public void expireOverdueVip() {
        try {
            int n = supabaseVipService.expireOverdueUsers();
            log.info("VipExpireJob 完成，处理过期会员数: {}", n);
        } catch (Exception e) {
            log.error("VipExpireJob 执行异常: {}", e.toString());
        }
    }
}