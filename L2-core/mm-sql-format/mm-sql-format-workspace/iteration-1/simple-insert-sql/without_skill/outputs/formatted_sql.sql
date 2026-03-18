-- =====================================================
-- 脚本名称: 企业基础信息数据同步
-- 功能描述: 从ODS层同步企业基础信息到DWS层
-- 目标表:   yidun_dw.dws_yidun_corp_basic_info_dd
-- 来源表:   yidun_ods.ods_yidun_corp_info_dd
-- 执行周期: 日增量 (按天分区)
-- 分区字段: pt_d (格式: yyyy-MM-dd)
-- 参数说明: ${pre_1day} - 前一天的日期
-- =====================================================

-- 开启小文件合并功能
-- 说明: 在MapReduce任务结束后自动合并小文件，减少HDFS上的小文件数量
--       避免NameNode内存压力过大，提升查询性能
set hive.merge.mapredfiles = true;

-- 数据同步: 覆盖写入目标表分区
-- 注意: INSERT OVERWRITE 会清空目标分区的原有数据后重新写入
insert OVERWRITE table yidun_dw.dws_yidun_corp_basic_info_dd PARTITION (pt_d = '${pre_1day}')
select
    -- 企业云用户ID，企业唯一标识
    clouduserid,
    -- 企业名称
    corpname,
    -- 会员等级（如：普通版、专业版、企业版等）
    membershipgrade,
    -- 行业标识/行业分类标记
    industry_flag,
    -- 企业负责人姓名
    owner_name
from yidun_ods.ods_yidun_corp_basic_info_dd  -- ODS层企业信息表
where pt_d = '${pre_1day}';  -- 过滤前一天的数据分区
