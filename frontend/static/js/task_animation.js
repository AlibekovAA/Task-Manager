function createCompletionAnimation(taskElement) {
    const particleContainer = document.createElement('div');
    particleContainer.className = 'particle-container';
    Object.assign(particleContainer.style, {
        position: 'fixed',
        top: '0',
        left: '0',
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: '9999',
    });
    document.body.appendChild(particleContainer);

    const rect = taskElement.getBoundingClientRect();
    const colors = ['#2ecc71', '#27ae60', '#ffffff', '#f1c40f', '#f39c12'];
    const particleCount = 20;
    const starCount = 10;
    const particles = [];

    const createParticle = (isGlitter, color, size, angle, speed, type) => ({
        element: document.createElement('div'),
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        gravity: type === 'star' ? 0.1 : 0.15,
        friction: type === 'star' ? 0.99 : 0.98,
        opacity: 1,
        scale: 1 + Math.random(),
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * (type === 'star' ? 20 : 15),
        color,
        isGlitter,
        type,
    });

    for (let i = 0; i < particleCount; i++) {
        const isGlitter = Math.random() < 0.3;
        const color = colors[Math.floor(Math.random() * colors.length)];
        const size = isGlitter ? '6px' : '10px';
        const particle = createParticle(isGlitter, color, size, (i / particleCount) * Math.PI * 2, 3 + Math.random() * 3, 'circle');

        particle.element.className = 'particle';
        Object.assign(particle.element.style, {
            position: 'absolute',
            width: size,
            height: size,
            background: color,
            borderRadius: '50%',
            pointerEvents: 'none',
            boxShadow: `0 0 ${isGlitter ? '15px' : '10px'} ${color}80`,
            transformOrigin: 'center',
        });
        particleContainer.appendChild(particle.element);
        particles.push(particle);
    }

    for (let i = 0; i < starCount; i++) {
        const color = colors[Math.floor(Math.random() * colors.length)];
        const size = 12 + Math.random() * 8;
        const star = createParticle(false, color, size, (i / starCount) * Math.PI * 2, 2 + Math.random() * 2, 'star');

        star.element.className = 'particle star';
        Object.assign(star.element.style, {
            position: 'absolute',
            width: `${size}px`,
            height: `${size}px`,
            background: color,
            clipPath: 'polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)',
            pointerEvents: 'none',
            boxShadow: `0 0 20px ${color}80`,
        });
        particleContainer.appendChild(star.element);
        particles.push(star);
    }

    const flash = document.createElement('div');
    Object.assign(flash.style, {
        position: 'absolute',
        left: `${rect.left}px`,
        top: `${rect.top}px`,
        width: `${rect.width}px`,
        height: `${rect.height}px`,
        background: 'white',
        borderRadius: '4px',
        opacity: '0.8',
        pointerEvents: 'none',
    });
    particleContainer.appendChild(flash);

    setTimeout(() => {
        flash.style.opacity = '0';
        flash.style.transition = 'opacity 0.3s ease-out';
        setTimeout(() => flash.remove(), 300);
    }, 50);

    const audio = new Audio('/static/sounds/completion.mp3');
    audio.volume = 0.2;
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

            particle.opacity -= particle.type === 'star' ? 0.008 : 0.01;

            if (particle.opacity > 0) {
                allParticlesDead = false;
                particle.element.style.transform = `translate(${particle.x}px, ${particle.y}px) rotate(${particle.rotation}deg) scale(${particle.scale})`;
                particle.element.style.opacity = particle.opacity;

                if (particle.type === 'star') {
                    particle.scale = 1 + Math.sin(frame * 0.1) * 0.2;
                }
            } else {
                particle.element.style.display = 'none';
            }
        });

        if (allParticlesDead || frame > 150) {
            particleContainer.remove();
        } else {
            requestAnimationFrame(animate);
        }
    };

    requestAnimationFrame(animate);
}
