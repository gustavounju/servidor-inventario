(function () {
    function applyTheme(themeName) {
        var finalTheme = themeName || localStorage.getItem('theme') || 'oceanic';
        document.documentElement.setAttribute('data-theme', finalTheme);
        localStorage.setItem('theme', finalTheme);
    }

    window.setTheme = applyTheme;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            applyTheme();
        });
    } else {
        applyTheme();
    }
})();
