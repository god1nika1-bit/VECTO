'use strict';

// ========================================
// DYNAMIC FOOTER YEAR
// ========================================
document.querySelector('.footer-copy').innerHTML =
    `© ${new Date().getFullYear()} VECTO. Цифровая архитектура для бизнеса.`;

// ========================================
// NAVIGATION SCROLL
// ========================================
const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 60);
});

// ========================================
// MOBILE MENU
// ========================================
const burger = document.getElementById('burger');
const mobileMenu = document.getElementById('mobileMenu');
const mobileMenuClose = document.getElementById('mobileMenuClose');
const mobileMenuLinks = mobileMenu.querySelectorAll('a');

function openMobileMenu() {
    mobileMenu.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeMobileMenu() {
    mobileMenu.classList.remove('open');
    document.body.style.overflow = '';
}

burger.addEventListener('click', openMobileMenu);
mobileMenuClose.addEventListener('click', closeMobileMenu);
mobileMenuLinks.forEach(link => {
    link.addEventListener('click', closeMobileMenu);
});

// ========================================
// HERO CANVAS ANIMATION (mobile optimized)
// ========================================
const canvas = document.getElementById('heroCanvas');
const ctx = canvas.getContext('2d');
const heroCard = document.querySelector('.hero-card');
const heroContent = document.querySelector('.hero-content');
let nodes = [];
let animId;
let textZones = [];
const isMobile = window.innerWidth < 768;
const NODE_COUNT = isMobile ? 40 : 80;
const CONNECT_DIST = isMobile ? 120 : 160;
const ACCENT_RGB = [0, 102, 255];

// Alpha range: text areas get MIN, empty areas get MAX
const ALPHA_MIN = 0.08;   // very subtle near text
const ALPHA_MAX = 0.95;   // very bright in empty space
const FADE_RADIUS = 160;  // wider smooth transition zone (px)

function resize() {
    const rect = heroCard.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
}

// Collect bounding rects of MAJOR text blocks relative to the canvas
function updateTextZones() {
    textZones = [];
    const cardRect = heroCard.getBoundingClientRect();
    // Only major text blocks — not every button/stat/link
    const elements = heroContent.querySelectorAll(
        'h1, .hero-description'
    );
    elements.forEach(el => {
        const r = el.getBoundingClientRect();
        const pad = 15;
        textZones.push({
            x: r.left - cardRect.left - pad,
            y: r.top - cardRect.top - pad,
            w: r.width + pad * 2,
            h: r.height + pad * 2
        });
    });
}

// Smooth ease-in-out curve for falloff
function smoothStep(t) {
    t = Math.max(0, Math.min(1, t));
    return t * t * (3 - 2 * t);
}

// Returns an alpha multiplier (0..1) based on how far a point is from text
function getIntensity(px, py) {
    let minDist = Infinity;
    for (let i = 0; i < textZones.length; i++) {
        const z = textZones[i];
        // Distance from point to nearest edge of the rect
        const cx = Math.max(z.x, Math.min(px, z.x + z.w));
        const cy = Math.max(z.y, Math.min(py, z.y + z.h));
        const dx = px - cx;
        const dy = py - cy;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < minDist) minDist = d;
    }
    // Inside a text zone → minDist = 0 → return ALPHA_MIN
    // Far from text → return ALPHA_MAX
    const t = smoothStep(Math.min(minDist / FADE_RADIUS, 1));
    return ALPHA_MIN + (ALPHA_MAX - ALPHA_MIN) * t;
}

function initNodes() {
    nodes = [];
    for (let i = 0; i < NODE_COUNT; i++) {
        nodes.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4,
            r: Math.random() * 2 + 0.8
        });
    }
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Update text zones periodically (every frame is cheap enough)
    updateTextZones();

    nodes.forEach(n => {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
        if (n.y < 0 || n.y > canvas.height) n.vy *= -1;
    });

    // Draw connections
    for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
            const dx = nodes[i].x - nodes[j].x;
            const dy = nodes[i].y - nodes[j].y;
            const d = Math.sqrt(dx * dx + dy * dy);
            if (d < CONNECT_DIST) {
                const midX = (nodes[i].x + nodes[j].x) / 2;
                const midY = (nodes[i].y + nodes[j].y) / 2;
                const intensity = getIntensity(midX, midY);
                const baseAlpha = (1 - d / CONNECT_DIST) * 0.65;
                const alpha = baseAlpha * intensity;
                ctx.beginPath();
                ctx.moveTo(nodes[i].x, nodes[i].y);
                ctx.lineTo(nodes[j].x, nodes[j].y);
                ctx.strokeStyle = `rgba(${ACCENT_RGB[0]},${ACCENT_RGB[1]},${ACCENT_RGB[2]},${alpha})`;
                ctx.lineWidth = intensity > 0.5 ? 1.0 : 0.7;
                ctx.stroke();
            }
        }
    }

    // Draw nodes with glow in bright areas
    nodes.forEach(n => {
        const intensity = getIntensity(n.x, n.y);
        const alpha = 0.85 * intensity;

        // Subtle glow around bright nodes
        if (intensity > 0.4) {
            const glowAlpha = (intensity - 0.4) * 0.25;
            ctx.beginPath();
            ctx.arc(n.x, n.y, n.r * 4, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${ACCENT_RGB[0]},${ACCENT_RGB[1]},${ACCENT_RGB[2]},${glowAlpha})`;
            ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${ACCENT_RGB[0]},${ACCENT_RGB[1]},${ACCENT_RGB[2]},${alpha})`;
        ctx.fill();
    });

    animId = requestAnimationFrame(draw);
}

window.addEventListener('resize', () => {
    cancelAnimationFrame(animId);
    resize();
    initNodes();
    draw();
});

resize();
initNodes();
draw();

// ========================================
// SCROLL REVEAL
// ========================================
const reveals = document.querySelectorAll('.reveal');
const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
        if (e.isIntersecting) {
            e.target.classList.add('visible');
            io.unobserve(e.target);
        }
    });
}, { threshold: 0.1 });
reveals.forEach(el => io.observe(el));

// Trigger hero immediately
setTimeout(() => {
    document.querySelectorAll('.hero-card .reveal').forEach(el => el.classList.add('visible'));
}, 100);

// ========================================
// STATS BAR COUNT-UP ANIMATION
// ========================================
const statsBar = document.getElementById('statsBar');
let statsAnimated = false;

function animateCountUp(el) {
    const target = parseInt(el.dataset.target);
    const suffix = el.dataset.suffix || '';
    const duration = 1500;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(eased * target);
        el.textContent = current + suffix;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    el.textContent = '0' + suffix;
    requestAnimationFrame(update);
}

const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => {
        if (e.isIntersecting && !statsAnimated) {
            statsAnimated = true;
            const numbers = statsBar.querySelectorAll('.stats-bar-number[data-target]');
            numbers.forEach(num => animateCountUp(num));
            statsObserver.unobserve(e.target);
        }
    });
}, { threshold: 0.3 });
statsObserver.observe(statsBar);

// ========================================
// ACCORDION
// ========================================
document.querySelectorAll('.accordion-header').forEach(btn => {
    btn.addEventListener('click', () => {
        const item = btn.parentElement;
        const body = item.querySelector('.accordion-body');
        const isOpen = item.classList.contains('open');

        const accordion = item.parentElement;
        accordion.querySelectorAll('.accordion-item').forEach(i => {
            i.classList.remove('open');
            i.querySelector('.accordion-body').style.maxHeight = null;
        });

        if (!isOpen) {
            item.classList.add('open');
            body.style.maxHeight = body.scrollHeight + 'px';
        }
    });
});

// ========================================
// CALCULATOR (with validation)
// ========================================
const calculatorSection = document.getElementById('calculator');

// Scroll to the top of the calculator section with nav offset
function scrollToCalculator() {
    const navHeight = document.getElementById('nav').offsetHeight;
    const top = calculatorSection.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;
    window.scrollTo({ top, behavior: 'smooth' });
}

const calcServices = document.getElementById('calcServices');
const calcExtras = document.getElementById('calcExtras');
const calcStep1 = document.getElementById('calcStep1');
const calcResult = document.getElementById('calcResult');
const calcTotalPrice = document.getElementById('calcTotalPrice');
const calcError = document.getElementById('calcError');

// Service selection
calcServices.querySelectorAll('.calc-option').forEach(opt => {
    opt.addEventListener('click', () => {
        opt.classList.toggle('selected');
        const service = opt.dataset.service;
        const extraGroup = document.querySelector(`.calc-extra-group[data-for="${service}"]`);
        if (extraGroup) {
            extraGroup.classList.toggle('show', opt.classList.contains('selected'));
            if (!opt.classList.contains('selected')) {
                extraGroup.querySelectorAll('.calc-extra-chip').forEach(c => c.classList.remove('selected'));
            }
        }
        // Hide error if something is selected
        if (opt.classList.contains('selected')) {
            calcError.classList.remove('show');
        }
    });
});

// Extra chips
calcExtras.querySelectorAll('.calc-extra-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        chip.classList.toggle('selected');
    });
});

// Calculate — don't switch screen without selection
document.getElementById('calcShowResult').addEventListener('click', () => {
    let total = 0;
    const selectedServices = calcServices.querySelectorAll('.calc-option.selected');

    if (selectedServices.length === 0) {
        // Show inline error, don't switch to result
        calcError.classList.add('show');
        setTimeout(() => {
            calcError.classList.remove('show');
        }, 3000);
        return;
    }

    selectedServices.forEach(opt => {
        total += parseInt(opt.dataset.price);
    });
    calcExtras.querySelectorAll('.calc-extra-chip.selected').forEach(chip => {
        total += parseInt(chip.dataset.extraPrice);
    });

    calcTotalPrice.innerHTML = `от <span class="accent">${total.toLocaleString('ru-RU')}</span> ₽`;
    calcTotalPrice.style.fontSize = '';

    calcStep1.style.display = 'none';
    calcResult.classList.add('active');

    // Scroll calc-result to center of viewport
    setTimeout(() => {
        const resultEl = document.getElementById('calcResult');
        const rect = resultEl.getBoundingClientRect();
        const scrollTarget = window.scrollY + rect.top - (window.innerHeight / 2) + (rect.height / 2);
        window.scrollTo({ top: scrollTarget, behavior: 'smooth' });
    }, 50);
});

// Reset
document.getElementById('calcReset').addEventListener('click', () => {
    calcResult.classList.remove('active');
    calcStep1.style.display = 'block';
    calcServices.querySelectorAll('.calc-option').forEach(o => o.classList.remove('selected'));
    calcExtras.querySelectorAll('.calc-extra-chip').forEach(c => c.classList.remove('selected'));
    calcExtras.querySelectorAll('.calc-extra-group').forEach(g => g.classList.remove('show'));

    // Scroll to top of calculator on reset too
    setTimeout(() => scrollToCalculator(), 50);
});
