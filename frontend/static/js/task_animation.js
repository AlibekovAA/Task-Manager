function createCompletionAnimation(taskElement) {
    const particleContainer = document.createElement('div');
    particleContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
    `;
    document.body.appendChild(particleContainer);

    const rect = taskElement.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const particleCount = 150;
    const particles = [];

    const colors = [
        '#FFD700',
        '#FF1493',
        '#00FF00',
        '#FF4500',
        '#1E90FF',
        '#FF00FF',
        '#00FFFF',
        '#FFFFFF'
    ];

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'completion-confetti';

        const isGlitter = Math.random() < 0.3;
        const isCircle = Math.random() < 0.5;

        const size = isGlitter ? Math.random() * 3 + 2 : Math.random() * 8 + 4;
        const color = colors[Math.floor(Math.random() * colors.length)];

        particle.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${isGlitter ? size : size * (Math.random() * 0.5 + 0.5)}px;
            background-color: ${color};
            transform: rotate(${Math.random() * 360}deg);
            border-radius: ${isCircle ? '50%' : '2px'};
            box-shadow: 0 0 ${isGlitter ? '10px' : '5px'} ${color};
            filter: brightness(${Math.random() * 0.5 + 1});
        `;

        const angle = (Math.PI * 2 * i) / particleCount;
        const velocity = 8 + Math.random() * 12;
        const spread = 1.2;

        particles.push({
            element: particle,
            x: centerX,
            y: centerY,
            vx: Math.cos(angle) * velocity * spread * (0.5 + Math.random()),
            vy: Math.sin(angle) * velocity * spread * (0.5 + Math.random()),
            rotation: Math.random() * 360,
            rotationSpeed: (Math.random() - 0.5) * 15,
            gravity: 0.2 + Math.random() * 0.1,
            friction: 0.99,
            opacity: 1,
            scale: 1,
            isGlitter
        });

        particleContainer.appendChild(particle);
    }

    const audio = new Audio('/static/sounds/completion.mp3');
    audio.volume = 0.3;
    audio.play().catch(() => console.log('Автовоспроизведение звука заблокировано браузером'));

    let frame = 0;
    const animate = () => {
        frame++;
        let allParticlesDead = true;

        particles.forEach(particle => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            particle.vy += particle.gravity;
            particle.vx *= particle.friction;
            particle.vy *= particle.friction;
            particle.rotation += particle.rotationSpeed;

            if (particle.isGlitter) {
                particle.scale = 1 + Math.sin(frame * 0.2) * 0.2;
            }

            particle.opacity -= 0.008;

            if (particle.opacity > 0) {
                allParticlesDead = false;
                particle.element.style.transform = `
                    translate(${particle.x}px, ${particle.y}px)
                    rotate(${particle.rotation}deg)
                    scale(${particle.scale})
                `;
                particle.element.style.opacity = particle.opacity;
            }
        });

        if (allParticlesDead || frame > 250) {
            particleContainer.remove();
        } else {
            requestAnimationFrame(animate);
        }
    };

    requestAnimationFrame(animate);
}
