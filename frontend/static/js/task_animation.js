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

    const particleCount = 100;
    const particles = [];
    const colors = [
        '#FFD700',
        '#FFA500',
        '#FF69B4',
        '#00FF00',
        '#87CEEB',
    ];

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'completion-confetti';
        particle.style.cssText = `
            position: absolute;
            width: ${Math.random() * 8 + 4}px;
            height: ${Math.random() * 8 + 4}px;
            background-color: ${colors[Math.floor(Math.random() * colors.length)]};
            transform: rotate(${Math.random() * 360}deg);
            border-radius: 2px;
            box-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
        `;

        const angle = (Math.PI * 2 * i) / particleCount;
        const velocity = 8 + Math.random() * 8;

        particles.push({
            element: particle,
            x: centerX,
            y: centerY,
            vx: Math.cos(angle) * velocity * (0.5 + Math.random()),
            vy: Math.sin(angle) * velocity * (0.5 + Math.random()),
            rotation: Math.random() * 360,
            rotationSpeed: (Math.random() - 0.5) * 10,
            gravity: 0.2,
            friction: 0.99,
            opacity: 1
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
            particle.opacity -= 0.01;

            if (particle.opacity > 0) {
                allParticlesDead = false;
                particle.element.style.transform = `translate(${particle.x}px, ${particle.y}px) rotate(${particle.rotation}deg)`;
                particle.element.style.opacity = particle.opacity;
            }
        });

        if (allParticlesDead || frame > 200) {
            particleContainer.remove();
        } else {
            requestAnimationFrame(animate);
        }
    };

    requestAnimationFrame(animate);
}
