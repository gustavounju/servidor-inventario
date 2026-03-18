(function () {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (!meta) {
        return;
    }

    var token = meta.getAttribute('content');
    if (!token) {
        return;
    }

    function attachCsrfToForms() {
        document.querySelectorAll('form').forEach(function (form) {
            var method = (form.getAttribute('method') || 'GET').toUpperCase();
            if (method !== 'POST') {
                return;
            }

            if (form.querySelector('input[name="csrf_token"]')) {
                return;
            }

            var input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'csrf_token';
            input.value = token;
            form.appendChild(input);
        });
    }

    var originalFetch = window.fetch;
    window.fetch = function (resource, options) {
        var finalOptions = options ? Object.assign({}, options) : {};
        var method = (finalOptions.method || 'GET').toUpperCase();
        var url = typeof resource === 'string' ? resource : ((resource && resource.url) || '');
        var sameOrigin = !url || url.indexOf('http://') !== 0 && url.indexOf('https://') !== 0 || url.indexOf(window.location.origin) === 0;

        if (sameOrigin && ['POST', 'PUT', 'PATCH', 'DELETE'].indexOf(method) >= 0) {
            var headers = new Headers(finalOptions.headers || {});
            if (!headers.has('X-CSRF-Token')) {
                headers.set('X-CSRF-Token', token);
            }
            finalOptions.headers = headers;
        }

        return originalFetch(resource, finalOptions);
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', attachCsrfToForms);
    } else {
        attachCsrfToForms();
    }
})();
