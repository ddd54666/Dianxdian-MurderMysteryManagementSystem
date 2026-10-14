"""Pydantic v2 请求校验模型。所有金额字段单位为分（INTEGER）。"""

import re
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


def _check_date_str(v, label):
    """校验日期字符串必须为 YYYY-MM-DD 且为有效日期。"""
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', v):
        raise ValueError(f'{label}格式必须为 YYYY-MM-DD')
    try:
        datetime.strptime(v, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f'{label}不是有效日期')
    return v


def _now_iso():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def _today_str():
    return date.today().strftime('%Y-%m-%d')


class ScriptCreate(BaseModel):
    """新增剧本"""
    name: str = Field(..., min_length=1, description='剧本名称')
    type: str = Field(..., description='剧本类型：欢乐/推理/恐怖/情感/机制')
    category: str = Field(..., description='剧本种类：盒装/城限')
    unit_price: int = Field(..., gt=0, description='常规单人价格（分）')
    player_count: int = Field(..., gt=0, description='剧本设计人数')
    is_player_count_fixed: bool = Field(True, description='人数是否固定')

    @field_validator('type')
    @classmethod
    def check_type(cls, v):
        if v not in ('欢乐', '推理', '恐怖', '情感', '机制'):
            raise ValueError('剧本类型必须是: 欢乐/推理/恐怖/情感/机制')
        return v

    @field_validator('category')
    @classmethod
    def check_category(cls, v):
        if v not in ('盒装', '城限'):
            raise ValueError('剧本种类必须是: 盒装/城限')
        return v


class ScriptUpdate(ScriptCreate):
    """编辑剧本（字段同新增）"""
    pass


class DMCreate(BaseModel):
    """新增DM"""
    name: str = Field(..., min_length=1, description='DM姓名')
    notes: str = Field('', description='备注')


class DMUpdate(BaseModel):
    """编辑DM"""
    name: str = Field(..., min_length=1, description='DM姓名')
    notes: str = Field('', description='备注')


class SessionCreate(BaseModel):
    """新增场次"""
    script_id: int = Field(..., gt=0, description='关联剧本ID')
    dm_count: int = Field(..., ge=1, le=6, description='DM人数(1-6)')
    dm_ids: List[int] = Field(..., min_length=1, max_length=6, description='DM ID列表')
    dm_salaries: List[int] = Field(default_factory=list, description='每DM薪资（分），与dm_ids等长')
    unit_price: int = Field(..., gt=0, description='本场单价（分）')
    player_count: int = Field(..., gt=0, description='本场人数')
    session_date: str = Field(..., description='开本日期 YYYY-MM-DD')
    revenue: int = Field(..., ge=0, description='场次营业额（分）')
    notes: str = Field('', description='备注')

    @field_validator('dm_salaries')
    @classmethod
    def check_dm_salaries(cls, v):
        """每DM薪资不允许负数。"""
        for s in v:
            if s < 0:
                raise ValueError('DM薪资不能为负数')
        return v

    @field_validator('session_date')
    @classmethod
    def check_session_date(cls, v):
        """开本日期必须为有效 YYYY-MM-DD。"""
        return _check_date_str(v, '开本日期')


class SessionUpdate(SessionCreate):
    """编辑场次（字段同新增）"""
    pass


class CarpoolCreate(BaseModel):
    """新增拼车"""
    carpool_date: str = Field(..., description='拼车日期 YYYY-MM-DD')
    script_id: int = Field(..., gt=0, description='关联剧本ID')
    notes: str = Field('', description='备注')

    @field_validator('carpool_date')
    @classmethod
    def check_carpool_date(cls, v):
        """拼车日期必须为有效 YYYY-MM-DD。"""
        return _check_date_str(v, '拼车日期')


class CarpoolUpdate(CarpoolCreate):
    """编辑拼车（字段同新增）"""
    pass


class MemberCreate(BaseModel):
    """新增会员"""
    name: str = Field(..., min_length=1, description='顾客姓名')
    gender: str = Field(..., description='性别：男/女')
    phone: str = Field(..., min_length=11, max_length=11, description='手机号11位')
    pay_amount: int = Field(..., gt=0, description='初始实付金额（分）')
    bonus_amount: int = Field(0, ge=0, description='初始赠送金额（分）')
    notes: str = Field('', description='备注')

    @field_validator('gender')
    @classmethod
    def check_gender(cls, v):
        if v not in ('男', '女'):
            raise ValueError('性别必须是: 男/女')
        return v

    @field_validator('phone')
    @classmethod
    def check_phone(cls, v):
        if not v.isdigit():
            raise ValueError('手机号必须为11位数字')
        return v


class MemberUpdate(BaseModel):
    """编辑会员信息（不修改余额）"""
    name: str = Field(..., min_length=1, description='顾客姓名')
    gender: str = Field(..., description='性别：男/女')
    phone: str = Field(..., min_length=11, max_length=11, description='手机号11位')
    notes: str = Field('', description='备注')

    @field_validator('gender')
    @classmethod
    def check_gender(cls, v):
        if v not in ('男', '女'):
            raise ValueError('性别必须是: 男/女')
        return v

    @field_validator('phone')
    @classmethod
    def check_phone(cls, v):
        if not v.isdigit():
            raise ValueError('手机号必须为11位数字')
        return v


class RechargeCreate(BaseModel):
    """新增充值"""
    recharge_time: str = Field(default_factory=_now_iso, description='充值时间 ISO')
    pay_amount: int = Field(..., gt=0, description='实付金额（分）')
    bonus_amount: int = Field(0, ge=0, description='赠送金额（分）')


class ConsumptionCreate(BaseModel):
    """新增消费"""
    consumption_time: str = Field(default_factory=_now_iso, description='消费时间 ISO')
    amount: int = Field(..., gt=0, description='消费金额（分）')
    script_name: str = Field(..., min_length=1, description='游玩剧本名称')


class MessageCreate(BaseModel):
    """新增留言"""
    author: str = Field(..., min_length=1, description='留言者')
    content: str = Field(..., min_length=1, description='留言内容')


class PasswordVerify(BaseModel):
    """二级密码验证"""
    password: str = Field(..., min_length=1, description='二级密码')
