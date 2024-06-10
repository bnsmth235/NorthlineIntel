let csiData = {};
fetch('/projectmanagement/get-master-format/')
    .then(response => response.json())
    .then(data => {
        csiData = data;
    })
    .catch(error => console.error('Error loading JSON:', error));

document.addEventListener('DOMContentLoaded', () => addEventListeners());
document.addEventListener('click', () => addEventListeners());

function addEventListeners(){
    const input = document.getElementById('csi');
    const descriptionDiv = document.getElementById('division-description');
    const suggestionsDiv = document.getElementById('autocomplete-suggestions');

    const displaySuggestions = (parts) => {
        let current = csiData;
        let description = '';
        let suggestions = [];

        for (let i = 0; i < parts.length; i++) {
            if (current[parts[i]]) {
                if (i === 0) {
                    description += current[parts[i]].name;
                    current = current[parts[i]];
                } else if (i === 1) {
                    description += ` > ${current[parts[i]].name}`;
                    current = current[parts[i]];
                } else if (i === 2) {
                    description += ` > ${current[parts[i]].name}`;
                }
            } else {
                break;
            }
        }

        descriptionDiv.innerText = description;

        // Autocomplete suggestions
        suggestionsDiv.innerHTML = '';
        if (parts.length === 0) {
            const divisions = Object.keys(csiData).filter(key => key !== 'name').sort((a, b) => a - b);
            suggestions = divisions.map(division => `${division} - ${csiData[division].name}`);
        } else if (parts.length === 1) {
            const division = parts[0];
            const divisions = Object.keys(csiData).filter(key => key.startsWith(division) && key !== 'name').sort((a, b) => a - b);
            suggestions = divisions.map(div => `${div} - ${csiData[div].name}`);
            if (csiData[division]) {
                const sections = Object.keys(csiData[division]).filter(key => key !== 'name').sort((a, b) => a - b);
                suggestions = sections.map(section => `${division} ${section} - ${csiData[division][section].name}`);
            }
        } else if (parts.length === 2) {
            const [division, section] = parts;
            if (csiData[division]) {
                const sections = Object.keys(csiData[division]).filter(key => key.startsWith(section) && key !== 'name').sort((a, b) => a - b);
                suggestions = sections.map(sec => `${division} ${sec} - ${csiData[division][sec].name}`);
                if (csiData[division][section]) {
                    const subsections = Object.keys(csiData[division][section]).filter(key => key !== 'name').sort((a, b) => a - b);
                    suggestions = subsections.map(subsec => `${division} ${section} ${subsec} - ${csiData[division][section][subsec].name}`);
                }
            }
        } else if (parts.length === 3) {
            const [division, section, subsection] = parts;
            if (csiData[division] && csiData[division][section]) {
                const subsections = Object.keys(csiData[division][section]).filter(key => key.startsWith(subsection) && key !== 'name').sort((a, b) => a - b);
                suggestions = subsections.map(subsec => `${division} ${section} ${subsec} - ${csiData[division][section][subsec].name}`);
            }
        }

        suggestions.forEach(suggestion => {
            const div = document.createElement('div');
            div.classList.add('autocomplete-suggestion');
            div.innerText = suggestion;
            div.addEventListener('click', () => {
                input.value = suggestion.split(' - ')[0];
                input.dispatchEvent(new Event('input'));
            });
            suggestionsDiv.appendChild(div);
        });
    };

    input.addEventListener('input', (e) => {
        const value = e.target.value.replace(/\s/g, '');
        const validValue = value.replace(/[^0-9]/g, '').slice(0, 6);
        const formattedValue = validValue.match(/.{1,2}/g)?.join(' ') || '';
        e.target.value = formattedValue;

        const parts = formattedValue.split(' ').filter(part => part.length > 0);
        displaySuggestions(parts);
    });

    document.addEventListener('click', (event) => {
        const input = document.getElementById('division-code');
        const suggestionsDiv = document.getElementById('autocomplete-suggestions');
        const isClickInsideInput = input.contains(event.target);
        const isClickInsideSuggestions = suggestionsDiv.contains(event.target);

        if (!isClickInsideInput && !isClickInsideSuggestions) {
            suggestionsDiv.style.display = 'none';
        }
    });

    input.addEventListener('focus', () => {
        const value = input.value.replace(/\s/g, '');
        const parts = value.match(/.{1,2}/g)?.filter(part => part.length > 0) || [];
        suggestionsDiv.style.display = '';
        displaySuggestions(parts);
    });
}