(function(root, factory) {
    const api = factory();
    if (typeof module === 'object' && module.exports) {
        module.exports = api;
    }
    if (root) {
        root.GoAgenticLearningPath = api;
    }
}(typeof globalThis !== 'undefined' ? globalThis : this, function() {
    const ROUTES = {
        application: [
            ...Array.from({ length: 16 }, (_, index) => index + 1),
            23, 24, 25
        ],
        fullstack: Array.from({ length: 25 }, (_, index) => index + 1),
        systems: [
            ...Array.from({ length: 12 }, (_, index) => index + 1),
            ...Array.from({ length: 6 }, (_, index) => index + 17)
        ]
    };

    function normalizePath(path) {
        return Object.prototype.hasOwnProperty.call(ROUTES, path) ? path : 'application';
    }

    function allowedChapters(path) {
        return ROUTES[normalizePath(path)].slice();
    }

    function isChapterAllowed(path, chapterNumber) {
        return allowedChapters(path).includes(Number(chapterNumber));
    }

    function chapterNumberFromHref(href) {
        const match = String(href || '').match(/(?:^|\/)chapter(\d+)(?:\/|$)/i);
        return match ? Number(match[1]) : null;
    }

    function adjacentChapter(path, currentChapter, direction) {
        const chapters = allowedChapters(path);
        const index = chapters.indexOf(Number(currentChapter));
        if (index < 0) return null;
        return chapters[index + (direction < 0 ? -1 : 1)] || null;
    }

    function pathFromHash(hash, storedPreference) {
        const match = String(hash || '').match(/[?&]id=route-(application|fullstack|systems)(?:&|$)/);
        return normalizePath(match ? match[1] : storedPreference);
    }

    return {
        allowedChapters,
        isChapterAllowed,
        chapterNumberFromHref,
        adjacentChapter,
        pathFromHash
    };
}));
