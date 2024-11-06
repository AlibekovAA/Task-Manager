document.addEventListener('DOMContentLoaded', () => {
    const logo = document.querySelector('.logo-ivti');
    if (logo) {
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

        logo.addEventListener('mouseover', startPulseAnimation);
        logo.addEventListener('mouseout', stopPulseAnimation);
    }
});
