(function() {
    if (!('cookieStore' in window)) return;

    function getLastCallerUrl() {
        const regex = /(https?:\/\/[^\s]+)/g;
        const stack = new Error().stack;
        const urls = stack.match(regex);
        return urls && urls.length ? urls[urls.length - 1] : '';
    }

    function getBaseDomain(hostname) {
        const parts = hostname.split('.');
        if (parts.length <= 2 || parts.every(part => !isNaN(parseInt(part, 10)))) {
            return hostname;
        }
        return parts.slice(-2).join('.');
    }

    function sendLog(cookieString, action) {
        const callerURL = getLastCallerUrl() || document.location.href;
        const visitingSiteDomain = getBaseDomain(window.location.hostname);
        window.postMessage({
            type: 'cookieAccess',
            logType: 'cookieStore',
            payload: {
                cookie: cookieString,
                initiatorURL: callerURL,
                visitingDomain: visitingSiteDomain,
                action: action,
                cookieType: 'cookieStore',
                accessType: 'script',
                timestamp: performance.now()
            }
        }, '*');
    }

    const originalGetAll = cookieStore.getAll;
    const originalGet  = cookieStore.get;
    const originalSet = cookieStore.set;
    const originalDelete = cookieStore.delete;

    cookieStore.getAll = async function (...args) {
        console.log('[Pouneh] cookieStore.getAll');
        const result = await originalGetAll.apply(this, args);
        result.forEach(cookie => sendLog(`${cookie.name}=${cookie.value}`, 'get'));
        return result
    };

    cookieStore.get = async function (...args) {
        console.log('[Pouneh] cookieStore.get');
        const result = await originalGet.apply(this, args);
        if (result)
            sendLog(`${result.name}=${result.value}`, 'get');
        return result;
    };

    cookieStore.set = async function (...args) {
        const details = args[0];
        if (details && details.name && 'value' in details) {
            console.log('[Pouneh] cookieStore.set');
            sendLog(`${details.name}=${details.value}`, 'set');
        }
        return originalSet.apply(this, args);
    };

    cookieStore.delete = async function (...args) {
        console.log('[Pouneh] cookieStore.delete');
        const name = args[0];
        sendLog(`${name}=`, 'delete');
        return originalDelete.apply(this, args);
    };

})();