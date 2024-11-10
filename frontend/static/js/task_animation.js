function createCompletionAnimation(taskElement) {
    const particleContainer = document.createElement('div');
    particleContainer.className = 'particle-container';
    particleContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: 9999;
    `;
    document.body.appendChild(particleContainer);

    const rect = taskElement.getBoundingClientRect();
    const particles = [];
    const colors = ['#2ecc71', '#27ae60', '#ffffff', '#f1c40f', '#f39c12'];

    const particleCount = 20;
    const starCount = 10;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        const isGlitter = Math.random() < 0.3;
        const color = colors[Math.floor(Math.random() * colors.length)];

        particle.className = 'particle';
        particle.style.cssText = `
            position: absolute;
            width: ${isGlitter ? '6px' : '10px'};
            height: ${isGlitter ? '6px' : '10px'};
            background: ${color};
            border-radius: 50%;
            pointer-events: none;
            box-shadow: 0 0 ${isGlitter ? '15px' : '10px'} ${color}80;
            transform-origin: center;
        `;

        particleContainer.appendChild(particle);

        const angle = (i / particleCount) * Math.PI * 2;
        const startX = rect.left + rect.width / 2;
        const startY = rect.top + rect.height / 2;
        const speed = 3 + Math.random() * 3;

        particles.push({
            element: particle,
            x: startX,
            y: startY,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            gravity: 0.15,
            friction: 0.98,
            opacity: 1,
            scale: 1 + Math.random(),
            rotation: Math.random() * 360,
            rotationSpeed: (Math.random() - 0.5) * 15,
            color: color,
            isGlitter,
            type: 'circle'
        });
    }

    for (let i = 0; i < starCount; i++) {
        const star = document.createElement('div');
        const color = colors[Math.floor(Math.random() * colors.length)];
        const size = 12 + Math.random() * 8;

        star.className = 'particle star';
        star.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            background: ${color};
            clip-path: polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%);
            pointer-events: none;
            box-shadow: 0 0 20px ${color}80;
        `;

        particleContainer.appendChild(star);

        const angle = (i / starCount) * Math.PI * 2;
        const startX = rect.left + rect.width / 2;
        const startY = rect.top + rect.height / 2;
        const speed = 2 + Math.random() * 2;

        particles.push({
            element: star,
            x: startX,
            y: startY,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            gravity: 0.1,
            friction: 0.99,
            opacity: 1,
            scale: 1,
            rotation: Math.random() * 360,
            rotationSpeed: (Math.random() - 0.5) * 20,
            color: color,
            type: 'star'
        });
    }

    const flash = document.createElement('div');
    flash.style.cssText = `
        position: absolute;
        left: ${rect.left}px;
        top: ${rect.top}px;
        width: ${rect.width}px;
        height: ${rect.height}px;
        background: white;
        border-radius: 4px;
        opacity: 0.8;
        pointer-events: none;
    `;
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

            if (particle.type === 'star') {
                particle.opacity -= 0.008;
            } else {
                particle.opacity -= 0.01;
            }

            if (particle.opacity > 0) {
                allParticlesDead = false;
                particle.element.style.transform = `
                    translate(${particle.x}px, ${particle.y}px)
                    rotate(${particle.rotation}deg)
                    scale(${particle.scale})
                `;
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
