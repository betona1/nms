/* NMS Settings Page JavaScript */
(function () {
    'use strict';

    const API = '/nms/api';

    // === Channel Management ===

    window.showAddChannel = function (type) {
        document.getElementById('add-channel-type').value = type;
        document.getElementById('add-channel-title').textContent =
            type === 'telegram' ? 'Telegram 채널 추가' : 'Discord 채널 추가';
        document.getElementById('telegram-fields').style.display = type === 'telegram' ? 'block' : 'none';
        document.getElementById('discord-fields').style.display = type === 'discord' ? 'block' : 'none';
        document.getElementById('add-channel-name').value = '';
        document.getElementById('add-tg-token').value = '';
        document.getElementById('add-tg-chatid').value = '';
        document.getElementById('add-dc-webhook').value = '';
        document.getElementById('add-channel-modal').style.display = 'flex';
    };

    window.closeAddChannel = function () {
        document.getElementById('add-channel-modal').style.display = 'none';
    };

    window.saveChannel = function () {
        const type = document.getElementById('add-channel-type').value;
        const name = document.getElementById('add-channel-name').value.trim();
        if (!name) return alert('채널 이름을 입력하세요.');

        const payload = {
            name: name,
            channel_type: type,
            is_active: false,
        };

        if (type === 'telegram') {
            payload.telegram_bot_token = document.getElementById('add-tg-token').value.trim();
            payload.telegram_chat_id = document.getElementById('add-tg-chatid').value.trim();
            if (!payload.telegram_bot_token || !payload.telegram_chat_id) {
                return alert('Bot Token과 Chat ID를 모두 입력하세요.');
            }
        } else {
            payload.discord_webhook_url = document.getElementById('add-dc-webhook').value.trim();
            if (!payload.discord_webhook_url) {
                return alert('Webhook URL을 입력하세요.');
            }
        }

        fetch(`${API}/channels/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        })
            .then(r => r.json())
            .then(() => { closeAddChannel(); location.reload(); })
            .catch(e => alert('저장 실패: ' + e));
    };

    window.toggleChannel = function (id, active) {
        fetch(`${API}/channels/${id}/`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: active }),
        }).catch(e => alert('변경 실패: ' + e));
    };

    window.deleteChannel = function (id) {
        if (!confirm('이 채널을 삭제하시겠습니까?')) return;
        fetch(`${API}/channels/${id}/`, { method: 'DELETE' })
            .then(() => location.reload())
            .catch(e => alert('삭제 실패: ' + e));
    };

    window.testChannel = function (id) {
        fetch(`${API}/notify/test/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channel_id: id }),
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert('테스트 메시지 전송 성공!');
                } else {
                    alert('전송 실패: ' + data.result);
                }
            })
            .catch(e => alert('오류: ' + e));
    };

    // === Subscription Management ===

    let currentSubs = {};

    window.loadSubscriptions = function () {
        const channelId = document.getElementById('sub-channel-select').value;
        const matrix = document.getElementById('sub-matrix');
        if (!channelId) {
            matrix.innerHTML = '<div class="no-data">위에서 채널을 선택하세요.</div>';
            return;
        }

        // Fetch targets and existing subscriptions
        Promise.all([
            fetch(`${API}/targets/`).then(r => r.json()),
            fetch(`${API}/subscriptions/?channel=${channelId}`).then(r => r.json()),
        ]).then(([targetsData, subsData]) => {
            const targets = targetsData.results || targetsData;
            const subs = subsData.results || subsData;

            // Build lookup
            const subMap = {};
            subs.forEach(s => { subMap[s.target || 'null'] = s; });

            let html = '';

            // External alerts subscription
            const extSub = subMap['null'] || {};
            html += buildSubRow(null, '전체 외부 알림 (ai100 등)', extSub);

            // Group targets
            const groups = {};
            targets.forEach(t => {
                if (!groups[t.group]) groups[t.group] = [];
                groups[t.group].push(t);
            });

            const groupLabels = { server: 'Servers', service: 'Services', domain: 'Domains', cctv: 'CCTV', router: 'Routers' };
            const groupOrder = ['server', 'service', 'domain', 'cctv', 'router'];

            groupOrder.forEach(g => {
                if (!groups[g]) return;
                html += `<div class="sub-group-label">${groupLabels[g] || g}</div>`;
                groups[g].forEach(t => {
                    const sub = subMap[t.id] || {};
                    html += buildSubRow(t.id, t.name, sub);
                });
            });

            matrix.innerHTML = html;
        }).catch(e => {
            matrix.innerHTML = '<div class="no-data">로딩 실패: ' + e + '</div>';
        });
    };

    function buildSubRow(targetId, name, sub) {
        const checked = sub.is_active ? 'checked' : '';
        const level = sub.min_level || 'critical';
        const tid = targetId === null ? 'null' : targetId;
        return `<div class="sub-row">
            <label class="sub-check">
                <input type="checkbox" data-target="${tid}" ${checked}>
                <span>${escapeHtml(name)}</span>
            </label>
            <select class="sub-level" data-target="${tid}">
                <option value="info" ${level === 'info' ? 'selected' : ''}>info 이상</option>
                <option value="warning" ${level === 'warning' ? 'selected' : ''}>warning 이상</option>
                <option value="critical" ${level === 'critical' ? 'selected' : ''}>critical만</option>
            </select>
        </div>`;
    }

    window.selectAllSubs = function (checked) {
        document.querySelectorAll('#sub-matrix input[type="checkbox"]').forEach(cb => {
            cb.checked = checked;
        });
    };

    window.saveSubscriptions = function () {
        const channelId = document.getElementById('sub-channel-select').value;
        if (!channelId) return alert('채널을 선택하세요.');

        const subs = [];
        document.querySelectorAll('#sub-matrix .sub-row').forEach(row => {
            const cb = row.querySelector('input[type="checkbox"]');
            const sel = row.querySelector('select');
            const tid = cb.dataset.target;
            subs.push({
                target_id: tid === 'null' ? null : parseInt(tid),
                is_active: cb.checked,
                min_level: sel.value,
            });
        });

        fetch(`${API}/notify/bulk-subscribe/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channel_id: parseInt(channelId), subscriptions: subs }),
        })
            .then(r => r.json())
            .then(data => {
                if (data.ok) alert('저장되었습니다.');
                else alert('저장 실패');
            })
            .catch(e => alert('오류: ' + e));
    };

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Modal close on overlay click
    const modal = document.getElementById('add-channel-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeAddChannel();
        });
    }
})();
