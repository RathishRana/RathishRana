// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {

    // ===== Mobile Navigation Toggle =====
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');

    navToggle.addEventListener('click', function() {
        navMenu.classList.toggle('active');

        // Animate hamburger menu
        const spans = navToggle.querySelectorAll('span');
        spans[0].style.transform = navMenu.classList.contains('active') ? 'rotate(45deg) translate(5px, 5px)' : 'none';
        spans[1].style.opacity = navMenu.classList.contains('active') ? '0' : '1';
        spans[2].style.transform = navMenu.classList.contains('active') ? 'rotate(-45deg) translate(7px, -6px)' : 'none';
    });

    // Close mobile menu when clicking on a link
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            navMenu.classList.remove('active');
            const spans = navToggle.querySelectorAll('span');
            spans[0].style.transform = 'none';
            spans[1].style.opacity = '1';
            spans[2].style.transform = 'none';
        });
    });

    // ===== Sticky Navigation =====
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', function() {
        if (window.scrollY > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // ===== Smooth Scrolling =====
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && document.querySelector(href)) {
                e.preventDefault();
                const target = document.querySelector(href);
                const offsetTop = target.offsetTop - 80;

                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });

    // ===== Countdown Timer =====
    function updateCountdown() {
        // Set conference date (June 15, 2025)
        const conferenceDate = new Date('2025-06-15T09:00:00').getTime();
        const now = new Date().getTime();
        const distance = conferenceDate - now;

        // Calculate time units
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        // Update DOM elements
        document.getElementById('days').textContent = String(days).padStart(2, '0');
        document.getElementById('hours').textContent = String(hours).padStart(2, '0');
        document.getElementById('minutes').textContent = String(minutes).padStart(2, '0');
        document.getElementById('seconds').textContent = String(seconds).padStart(2, '0');

        // Check if countdown is finished
        if (distance < 0) {
            clearInterval(countdownInterval);
            document.getElementById('countdown').innerHTML = '<h2>Conference is Live!</h2>';
        }
    }

    // Update countdown every second
    updateCountdown();
    const countdownInterval = setInterval(updateCountdown, 1000);

    // ===== Animated Counter =====
    const counters = document.querySelectorAll('.counter');
    const speed = 200; // Animation speed
    let animated = false;

    function animateCounters() {
        if (animated) return;

        const aboutSection = document.getElementById('about');
        const sectionPos = aboutSection.getBoundingClientRect().top;
        const screenPos = window.innerHeight / 1.3;

        if (sectionPos < screenPos) {
            counters.forEach(counter => {
                const target = +counter.getAttribute('data-target');
                const increment = target / speed;
                let count = 0;

                const updateCounter = () => {
                    count += increment;
                    if (count < target) {
                        counter.textContent = Math.ceil(count);
                        setTimeout(updateCounter, 10);
                    } else {
                        counter.textContent = target + '+';
                    }
                };

                updateCounter();
            });
            animated = true;
        }
    }

    window.addEventListener('scroll', animateCounters);

    // ===== Schedule Tabs =====
    const tabButtons = document.querySelectorAll('.tab-button');
    const scheduleDays = document.querySelectorAll('.schedule-day');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const day = this.getAttribute('data-day');

            // Remove active class from all buttons and days
            tabButtons.forEach(btn => btn.classList.remove('active'));
            scheduleDays.forEach(scheduleDay => scheduleDay.classList.remove('active'));

            // Add active class to clicked button and corresponding day
            this.classList.add('active');
            document.getElementById(day).classList.add('active');
        });
    });

    // ===== Registration Form Validation =====
    const registrationForm = document.getElementById('registrationForm');
    const formMessage = document.getElementById('formMessage');

    registrationForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Get form values
        const firstName = document.getElementById('firstName').value.trim();
        const lastName = document.getElementById('lastName').value.trim();
        const email = document.getElementById('email').value.trim();
        const ticketType = document.getElementById('ticketType').value;
        const terms = document.getElementById('terms').checked;

        // Validation
        if (!firstName || !lastName) {
            showMessage('Please enter your full name.', 'error');
            return;
        }

        if (!validateEmail(email)) {
            showMessage('Please enter a valid email address.', 'error');
            return;
        }

        if (!ticketType) {
            showMessage('Please select a ticket type.', 'error');
            return;
        }

        if (!terms) {
            showMessage('Please accept the terms and conditions.', 'error');
            return;
        }

        // Simulate form submission
        const submitButton = registrationForm.querySelector('.btn-submit');
        submitButton.textContent = 'Processing...';
        submitButton.disabled = true;

        setTimeout(() => {
            showMessage(`Thank you, ${firstName}! Your registration has been received. Check your email for confirmation.`, 'success');
            registrationForm.reset();
            submitButton.textContent = 'Complete Registration';
            submitButton.disabled = false;

            // Store registration data (in real app, would send to server)
            const registrationData = {
                firstName,
                lastName,
                email,
                ticketType,
                company: document.getElementById('company').value,
                dietary: document.getElementById('dietary').value,
                newsletter: document.getElementById('newsletter').checked,
                timestamp: new Date().toISOString()
            };

            console.log('Registration Data:', registrationData);
        }, 2000);
    });

    // Email validation helper function
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    // Show form message
    function showMessage(message, type) {
        formMessage.textContent = message;
        formMessage.className = `form-message ${type}`;
        formMessage.style.display = 'block';

        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                formMessage.style.display = 'none';
            }, 5000);
        }
    }

    // ===== Newsletter Form =====
    const newsletterForm = document.getElementById('newsletterForm');

    newsletterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const email = this.querySelector('input[type="email"]').value;

        if (validateEmail(email)) {
            alert('Thank you for subscribing to our newsletter!');
            this.reset();
        } else {
            alert('Please enter a valid email address.');
        }
    });

    // ===== Scroll to Top Button =====
    const scrollTopBtn = document.getElementById('scrollTopBtn');

    window.addEventListener('scroll', function() {
        if (window.scrollY > 300) {
            scrollTopBtn.classList.add('show');
        } else {
            scrollTopBtn.classList.remove('show');
        }
    });

    scrollTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // ===== Scroll Animation for Elements =====
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe elements for scroll animations
    const animatedElements = document.querySelectorAll('.about-card, .speaker-card, .schedule-item, .pricing-card');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });

    // ===== Dynamic Speaker Hover Effects =====
    const speakerCards = document.querySelectorAll('.speaker-card');

    speakerCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // ===== Schedule Item Click for Mobile =====
    const scheduleItems = document.querySelectorAll('.schedule-item');

    scheduleItems.forEach(item => {
        item.addEventListener('click', function() {
            // Add a subtle pulse effect
            this.style.animation = 'pulse 0.3s ease';
            setTimeout(() => {
                this.style.animation = '';
            }, 300);
        });
    });

    // Add pulse animation to CSS dynamically
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }
    `;
    document.head.appendChild(style);

    // ===== Real-time Form Validation =====
    const formInputs = registrationForm.querySelectorAll('input[required], select[required]');

    formInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value.trim() === '') {
                this.style.borderColor = '#E94B3C';
            } else {
                this.style.borderColor = '#6BCF7F';
            }
        });

        input.addEventListener('input', function() {
            if (this.value.trim() !== '') {
                this.style.borderColor = '#6BCF7F';
            }
        });
    });

    // Email field real-time validation
    const emailInput = document.getElementById('email');
    emailInput.addEventListener('input', function() {
        if (validateEmail(this.value)) {
            this.style.borderColor = '#6BCF7F';
        } else if (this.value.trim() !== '') {
            this.style.borderColor = '#E94B3C';
        }
    });

    // ===== Pricing Card Selection =====
    const pricingCards = document.querySelectorAll('.pricing-card');
    const ticketTypeSelect = document.getElementById('ticketType');

    pricingCards.forEach(card => {
        card.addEventListener('click', function() {
            // Determine ticket type based on card
            const cardTitle = this.querySelector('h3').textContent.toLowerCase();
            let ticketValue = '';

            if (cardTitle.includes('early')) {
                ticketValue = 'early-bird';
            } else if (cardTitle.includes('standard')) {
                ticketValue = 'standard';
            } else if (cardTitle.includes('vip')) {
                ticketValue = 'vip';
            }

            // Update select dropdown
            ticketTypeSelect.value = ticketValue;

            // Scroll to registration form
            const registrationSection = document.getElementById('register');
            const formElement = document.querySelector('.registration-form');

            window.scrollTo({
                top: formElement.offsetTop - 100,
                behavior: 'smooth'
            });

            // Highlight the form briefly
            formElement.style.boxShadow = '0 0 30px rgba(74, 144, 226, 0.5)';
            setTimeout(() => {
                formElement.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.1)';
            }, 1500);
        });
    });

    // ===== Active Navigation Link Highlighting =====
    const sections = document.querySelectorAll('section[id]');

    window.addEventListener('scroll', () => {
        let current = '';

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;

            if (window.scrollY >= sectionTop - 100) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });

    // ===== Loading Animation =====
    window.addEventListener('load', function() {
        document.body.style.opacity = '0';
        setTimeout(() => {
            document.body.style.transition = 'opacity 0.5s ease';
            document.body.style.opacity = '1';
        }, 100);
    });

    // ===== Dynamic Date Updates =====
    const currentYear = new Date().getFullYear();
    document.querySelectorAll('.footer-bottom p').forEach(p => {
        if (p.textContent.includes('2025')) {
            p.textContent = p.textContent.replace('2025', currentYear);
        }
    });

    // ===== Console Welcome Message =====
    console.log('%c🎉 Welcome to Tech Conference 2025! 🎉', 'color: #4A90E2; font-size: 20px; font-weight: bold;');
    console.log('%cBuilt with ❤️ for an amazing conference experience', 'color: #666; font-size: 12px;');

    // ===== Performance Monitoring =====
    window.addEventListener('load', function() {
        const loadTime = window.performance.timing.domContentLoadedEventEnd - window.performance.timing.navigationStart;
        console.log(`Page loaded in ${loadTime}ms`);
    });

    // ===== Keyboard Navigation Support =====
    document.addEventListener('keydown', function(e) {
        // Press 'Escape' to close mobile menu
        if (e.key === 'Escape' && navMenu.classList.contains('active')) {
            navMenu.classList.remove('active');
        }

        // Press 'R' to scroll to registration
        if (e.key === 'r' && e.ctrlKey) {
            e.preventDefault();
            document.getElementById('register').scrollIntoView({ behavior: 'smooth' });
        }
    });

    // ===== Add Fade-in Effect to Hero Content =====
    setTimeout(() => {
        const heroContent = document.querySelector('.hero-content');
        heroContent.style.opacity = '1';
    }, 200);

    // ===== Interactive Ticket Price Display =====
    const ticketSelect = document.getElementById('ticketType');

    ticketSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        if (selectedOption.value) {
            console.log(`Selected ticket: ${selectedOption.text}`);
        }
    });

});

// ===== Service Worker Registration (for PWA capability) =====
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        // Uncomment the line below to register a service worker
        // navigator.serviceWorker.register('/service-worker.js');
    });
}

// ===== Utility Functions =====

// Debounce function for performance optimization
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function for scroll events
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Format date function
function formatDate(date) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(date).toLocaleDateString('en-US', options);
}

// ===== Export for Testing (if using modules) =====
// export { validateEmail, formatDate, debounce, throttle };
