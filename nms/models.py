from django.db import models

CHECK_TYPE_CHOICES = [
    ('ping', 'Ping'),
    ('port', 'Port'),
    ('http', 'HTTP'),
    ('resource', 'Resource'),
    ('sms_device', 'SMS Device'),
]

STATUS_CHOICES = [
    ('up', 'Up'),
    ('down', 'Down'),
    ('warn', 'Warning'),
    ('unknown', 'Unknown'),
]

ALERT_LEVEL_CHOICES = [
    ('info', 'Info'),
    ('warning', 'Warning'),
    ('critical', 'Critical'),
]

CONDITION_CHOICES = [
    ('down', 'Down'),
    ('cpu_over', 'CPU Over'),
    ('mem_over', 'Memory Over'),
    ('disk_over', 'Disk Over'),
]

GROUP_CHOICES = [
    ('server', 'Server'),
    ('service', 'Service'),
    ('domain', 'Domain'),
    ('cctv', 'CCTV'),
    ('router', 'Router'),
]

PRIORITY_CHOICES = [
    ('lg', 'Large'),
    ('md', 'Medium'),
    ('sm', 'Small'),
]


class MonitorTarget(models.Model):
    name = models.CharField('대상명', max_length=100)
    host = models.CharField('호스트', max_length=255)
    port = models.IntegerField('포트', null=True, blank=True)
    check_type = models.CharField('체크 타입', max_length=20, choices=CHECK_TYPE_CHOICES, default='ping')
    check_url = models.CharField('체크 URL', max_length=500, blank=True, default='')
    group = models.CharField('그룹', max_length=20, choices=GROUP_CHOICES, default='server')
    interval = models.IntegerField('체크 주기(초)', default=60)
    is_active = models.BooleanField('활성화', default=True)
    last_status = models.CharField('최근 상태', max_length=10, choices=STATUS_CHOICES, default='unknown')
    last_checked = models.DateTimeField('마지막 체크', null=True, blank=True)
    last_response_time = models.FloatField('최근 응답시간(ms)', null=True, blank=True)
    fail_count = models.IntegerField('연속 실패', default=0)
    priority = models.CharField('우선순위', max_length=2, choices=PRIORITY_CHOICES, default='sm')
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        db_table = 'monitor_targets'
        verbose_name = '모니터링 대상'
        verbose_name_plural = '모니터링 대상'
        ordering = ['group', 'host', 'port']

    def __str__(self):
        port_str = f':{self.port}' if self.port else ''
        return f'{self.name} ({self.host}{port_str})'


class AlertRule(models.Model):
    target = models.ForeignKey(MonitorTarget, on_delete=models.CASCADE,
                               related_name='alert_rules', verbose_name='대상')
    condition = models.CharField('조건', max_length=20, choices=CONDITION_CHOICES, default='down')
    threshold = models.IntegerField('임계값', default=0)
    level = models.CharField('레벨', max_length=10, choices=ALERT_LEVEL_CHOICES, default='critical')
    consecutive = models.IntegerField('연속 실패 후 알림', default=3)
    cooldown = models.IntegerField('재알림 방지(초)', default=300)
    is_active = models.BooleanField('활성화', default=True)
    last_triggered = models.DateTimeField('마지막 트리거', null=True, blank=True)

    class Meta:
        db_table = 'alert_rules'
        verbose_name = '알림 규칙'
        verbose_name_plural = '알림 규칙'

    def __str__(self):
        return f'{self.target.name} - {self.condition} ({self.level})'


class Alert(models.Model):
    target = models.ForeignKey(MonitorTarget, on_delete=models.CASCADE,
                               related_name='alerts', verbose_name='대상',
                               null=True, blank=True)
    rule = models.ForeignKey(AlertRule, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='alerts', verbose_name='규칙')
    level = models.CharField('레벨', max_length=10, choices=ALERT_LEVEL_CHOICES)
    title = models.CharField('제목', max_length=200)
    message = models.TextField('메시지')
    source = models.CharField('소스', max_length=50, blank=True, default='nms')
    sent_at = models.DateTimeField('발송 시각', auto_now_add=True)
    resolved_at = models.DateTimeField('복구 시각', null=True, blank=True)
    fcm_result = models.CharField('FCM 결과', max_length=500, blank=True, default='')

    class Meta:
        db_table = 'alerts'
        verbose_name = '알림 이력'
        verbose_name_plural = '알림 이력'
        ordering = ['-sent_at']

    def __str__(self):
        return f'[{self.level}] {self.title}'


class StatusLog(models.Model):
    target = models.ForeignKey(MonitorTarget, on_delete=models.CASCADE,
                               related_name='status_logs', verbose_name='대상')
    status = models.CharField('상태', max_length=10, choices=STATUS_CHOICES)
    response_time = models.FloatField('응답시간(ms)', null=True, blank=True)
    detail = models.TextField('상세', blank=True, default='')
    created_at = models.DateTimeField('기록일', auto_now_add=True)

    class Meta:
        db_table = 'status_logs'
        verbose_name = '상태 로그'
        verbose_name_plural = '상태 로그'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['target', '-created_at']),
        ]

    def __str__(self):
        return f'{self.target.name} - {self.status}'


class DeviceToken(models.Model):
    device = models.CharField('기기명', max_length=100, unique=True)
    token = models.TextField('FCM 토큰')
    is_active = models.BooleanField('활성화', default=True)
    updated_at = models.DateTimeField('갱신일', auto_now=True)

    class Meta:
        db_table = 'device_tokens'
        verbose_name = 'FCM 기기 토큰'
        verbose_name_plural = 'FCM 기기 토큰'

    def __str__(self):
        return f'{self.device}'


CHANNEL_TYPE_CHOICES = [
    ('telegram', 'Telegram'),
    ('discord', 'Discord'),
]


class NotificationChannel(models.Model):
    name = models.CharField('채널명', max_length=100)
    channel_type = models.CharField('채널 타입', max_length=20, choices=CHANNEL_TYPE_CHOICES)
    is_active = models.BooleanField('활성화', default=False)

    # Telegram
    telegram_bot_token = models.CharField('봇 토큰', max_length=200, blank=True, default='')
    telegram_chat_id = models.CharField('Chat ID', max_length=100, blank=True, default='')

    # Discord
    discord_webhook_url = models.URLField('Webhook URL', max_length=500, blank=True, default='')

    created_at = models.DateTimeField('생성일', auto_now_add=True)

    class Meta:
        db_table = 'notification_channels'
        verbose_name = '알림 채널'
        verbose_name_plural = '알림 채널'

    def __str__(self):
        return f'[{self.channel_type}] {self.name}'


class ChannelSubscription(models.Model):
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE,
                                 related_name='subscriptions', verbose_name='채널')
    target = models.ForeignKey(MonitorTarget, on_delete=models.CASCADE,
                                null=True, blank=True,
                                related_name='subscriptions', verbose_name='대상')
    is_active = models.BooleanField('활성화', default=True)
    min_level = models.CharField('최소 레벨', max_length=10,
                                  choices=ALERT_LEVEL_CHOICES, default='critical')

    class Meta:
        db_table = 'channel_subscriptions'
        verbose_name = '채널 구독'
        verbose_name_plural = '채널 구독'
        unique_together = ['channel', 'target']

    def __str__(self):
        target_name = self.target.name if self.target else '전체(외부 포함)'
        return f'{self.channel.name} → {target_name}'
