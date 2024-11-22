document.addEventListener('DOMContentLoaded', () => {
    const logo = document.querySelector('.logo-ivti');
    if (!logo) return;

    let isAnimating = false;

    const startPulseAnimation = () => {
        if (!isAnimating) {
            isAnimating = true;
            logo.style.animation = 'pulse 1.5s infinite';
            logo.style.filter = 'brightness(0) invert(1) drop-shadow(0 0 10px rgba(255, 255, 255, 0.7))';
        }
    };

    const stopPulseAnimation = () => {
        isAnimating = false;
        logo.style.animation = 'none';
        logo.style.filter = 'brightness(0) invert(0.7)';
    };

    const createFirework = (e) => {
        const canvas = document.createElement('canvas');
        Object.assign(canvas.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            width: '100%',
            height: '100%',
            pointerEvents: 'none',
            zIndex: '9999'
        });
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const ctx = canvas.getContext('2d');
        document.body.appendChild(canvas);

        const rect = logo.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff', '#ffffff'];
        const particles = Array.from({length: 50}, (_, i) => {
            const angle = (Math.PI * 2 * i) / 50;
            const velocity = 5 + Math.random() * 10;
            const color = colors[Math.floor(Math.random() * colors.length)];
            return {
                x: centerX,
                y: centerY,
                vx: Math.cos(angle) * velocity,
                vy: Math.sin(angle) * velocity,
                color,
                size: 2 + Math.random() * 2,
                alpha: 1
            };
        });

        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            let allParticlesDead = true;
            particles.forEach(particle => {
                particle.x += particle.vx;
                particle.y += particle.vy;
                particle.vy += 0.1;
                particle.alpha -= 0.01;

                if (particle.alpha > 0) {
                    allParticlesDead = false;
                    ctx.save();
                    ctx.globalAlpha = particle.alpha;
                    ctx.fillStyle = particle.color;
                    ctx.beginPath();
                    ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.restore();
                }
            });

            if (allParticlesDead) {
                canvas.remove();
            } else {
                requestAnimationFrame(animate);
            }
        };

        animate();
    };

    logo.addEventListener('mouseover', startPulseAnimation);
    logo.addEventListener('mouseout', stopPulseAnimation);
    logo.addEventListener('click', createFirework);
});
