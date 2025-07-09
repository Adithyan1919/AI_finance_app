function loadGoogleTranslate() {
    new google.translate.TranslateElement({
        pageLanguage: 'en',
        includedLanguages: 'en,ta,hi,ml,te',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE
    }, 'google_translate_element');
}

function translatePage(lang) {
    const translate = new google.translate.TranslateElement({
        pageLanguage: lang,
        includedLanguages: 'en,ta,hi,ml,te',
        autoDisplay: false
    });
    translate.translatePage(lang, 'en', () => {});
}

// Budget Chart
// Only fetch budget data if we're on the homepage
if (window.location.pathname === '/' || window.location.pathname === '/dashboard') {
    fetch('/budget-data')
        .then(response => response.json())
        .then(data => {
            // render your chart or data here
        });
}
