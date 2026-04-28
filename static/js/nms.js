/* NMS Dashboard JavaScript */
(function () {
    'use strict';

    // Clock
    function updateClock() {
        const el = document.getElementById('datetime');
        if (!el) return;
        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        el.textContent = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
    }
    setInterval(updateClock, 1000);
    updateClock();

    // Previous status cache for flash detection
    const prevStatus = {};

    // Fetch status and update dashboard
    function fetchStatus() {
        fetch('/nms/api/status/')
            .then(r => r.json())
            .then(data => {
                updateSummary(data.summary);
                updateBanner(data.summary);
                updateTargets(data.targets);
                updateAlerts(data.alerts);
                updateSmsPhones(data.sms_phones);
            })
            .catch(() => {});
    }

    function updateSummary(s) {
        setText('stat-total', s.total);
        setText('stat-up', s.up);
        setText('stat-down', s.down);
        setText('stat-warn', s.warn);
    }

    function updateBanner(s) {
        const banner = document.getElementById('status-banner');
        if (!banner) return;
        if (s.down > 0) {
            banner.innerHTML = '<span class="banner-dot banner-dot-down"></span><span>' + s.down + '개 서비스 장애 감지</span>';
        } else if (s.warn > 0) {
            banner.innerHTML = '<span class="banner-dot banner-dot-warn"></span><span>일부 서비스 주의 필요</span>';
        } else {
            banner.innerHTML = '<span class="banner-dot banner-dot-up"></span><span>All Systems Operational</span>';
        }
    }

    function updateTargets(targets) {
        targets.forEach(t => {
            const card = document.getElementById('card-' + t.id);
            if (!card) return;

            const oldStatus = card.dataset.status;
            const newStatus = t.last_status;

            // Update status
            card.dataset.status = newStatus;

            // Flash on change
            if (oldStatus !== newStatus && oldStatus !== 'unknown') {
                card.classList.remove('flash-up', 'flash-down');
                void card.offsetWidth; // reflow
                card.classList.add(newStatus === 'up' ? 'flash-up' : 'flash-down');
                if (newStatus === 'down') {
                    showToast(t.name + ' DOWN', false);
                } else if (newStatus === 'up' && oldStatus === 'down') {
                    showToast(t.name + ' RECOVERED', true);
                }
            }

            // Update status dot
            const dot = card.querySelector('.status-dot');
            if (dot) {
                dot.className = 'status-dot status-' + newStatus;
            }

            // Update response time
            const rt = document.getElementById('rt-' + t.id);
            if (rt) {
                rt.textContent = t.last_response_time ? (t.last_response_time.toFixed(1) + 'ms') : '-';
            }

            // Update last check
            const lc = document.getElementById('lc-' + t.id);
            if (lc && t.last_checked) {
                const d = new Date(t.last_checked);
                const pad = n => String(n).padStart(2, '0');
                lc.textContent = pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
            }
        });
    }

    function updateAlerts(alerts) {
        const list = document.getElementById('alert-list');
        if (!list || !alerts || alerts.length === 0) return;

        list.innerHTML = alerts.map(a => {
            const resolved = a.resolved_at
                ? '<span class="alert-resolved-badge">RESOLVED</span>'
                : '';
            const time = a.sent_at ? new Date(a.sent_at).toLocaleString('ko-KR', {
                month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
            }) : '';
            return `<div class="alert-item alert-${a.level}">
                <span class="alert-level-badge level-${a.level}">${a.level.toUpperCase()}</span>
                <span class="alert-title">${escapeHtml(a.title)}</span>
                <span class="alert-time">${time}</span>
                ${resolved}
            </div>`;
        }).join('');
    }

    function updateSmsPhones(phones) {
        if (!phones || phones.length === 0) return;
        // Find all sms-phones containers
        document.querySelectorAll('[id^="sms-phones-"]').forEach(el => {
            el.innerHTML = phones.map(p => {
                const cls = p.connected ? 'phone-connected' : 'phone-disconnected';
                const ago = p.seconds_ago < 60 ? p.seconds_ago + '초' :
                    Math.floor(p.seconds_ago / 60) + '분';
                const label = p.alias || p.phone_number;
                return `<span class="sms-phone-chip ${cls}"><span class="sms-phone-dot"></span>${escapeHtml(label)} ${ago}</span>`;
            }).join('');
        });
    }

    // Toast notification
    function showToast(message, isResolved) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        const toast = document.createElement('div');
        toast.className = 'nms-toast' + (isResolved ? ' toast-resolved' : '');
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('toast-fade');
            setTimeout(() => toast.remove(), 400);
        }, 4000);
    }

    // Helpers
    function setText(id, val) {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Domain card click → open URL
    document.querySelectorAll('.target-card.clickable').forEach(card => {
        card.style.cursor = 'pointer';
        card.addEventListener('click', () => {
            // NAT modal for main router
            if (card.dataset.nat === 'true') {
                const modal = document.getElementById('nat-modal');
                if (modal) modal.style.display = 'flex';
                return;
            }
            const url = card.dataset.url;
            if (url) window.open(url, '_blank');
        });
    });

    // NAT modal close
    const natModal = document.getElementById('nat-modal');
    const natClose = document.getElementById('nat-modal-close');
    if (natClose) {
        natClose.addEventListener('click', () => { natModal.style.display = 'none'; });
    }
    if (natModal) {
        natModal.addEventListener('click', (e) => {
            if (e.target === natModal) natModal.style.display = 'none';
        });
    }

    // Start polling
    if (document.getElementById('stat-total')) {
        setInterval(fetchStatus, 5000);
        // First fetch after 2 seconds
        setTimeout(fetchStatus, 2000);
    }
})();
