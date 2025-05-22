/**
 * KOmpanion - 主JavaScript文件
 */

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    console.log('KOmpanion应用已加载');
    
    // 平滑滚动到锚点
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80, // 减去头部高度
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // 响应式导航菜单
    const setupResponsiveNav = () => {
        const header = document.querySelector('header');
        if (!header) return;
        
        // 如果需要，可以创建一个汉堡菜单按钮
        if (!document.querySelector('.menu-toggle')) {
            const nav = document.querySelector('nav');
            const menuToggle = document.createElement('button');
            menuToggle.className = 'menu-toggle';
            menuToggle.innerHTML = '&#9776;'; // 汉堡图标
            menuToggle.style.display = 'none'; // 默认隐藏
            
            menuToggle.addEventListener('click', () => {
                nav.classList.toggle('active');
            });
            
            header.querySelector('.container').insertBefore(menuToggle, nav);
            
            // 添加媒体查询来切换显示
            const handleResize = () => {
                if (window.innerWidth <= 768) {
                    menuToggle.style.display = 'block';
                    nav.classList.add('mobile-nav');
                } else {
                    menuToggle.style.display = 'none';
                    nav.classList.remove('mobile-nav', 'active');
                }
            };
            
            window.addEventListener('resize', handleResize);
            handleResize(); // 初始检查
        }
    };
    
    // 初始化响应式导航
    setupResponsiveNav();
    
    // 添加滚动监听以突出显示当前部分
    const highlightCurrentSection = () => {
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('nav ul li a');
        
        window.addEventListener('scroll', () => {
            let current = '';
            const scrollPosition = window.scrollY + 100; // 添加偏移量
            
            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.offsetHeight;
                
                if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                    current = '#' + section.getAttribute('id');
                }
            });
            
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === current) {
                    link.classList.add('active');
                }
            });
        });
    };
    
    // 初始化滚动监听
    highlightCurrentSection();
});

// 响应式导航菜单（如果需要的话）
function toggleMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    if (navMenu) {
        navMenu.classList.toggle('active');
    }
} 