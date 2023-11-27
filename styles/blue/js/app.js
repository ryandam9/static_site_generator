// Function to create a Table of Contents
function generateTOC() {
    var toc = "<nav class='table-of-contents'><ul>";
    var headers = document.querySelector('.content-section').querySelectorAll('h1, h2, h3');
    var currentLevel = 1;

    headers.forEach(function (header) {
        var level = parseInt(header.tagName.substring(1));

        if (level > currentLevel) {
            for (var i = currentLevel; i < level; i++) {
                toc += "<ul>";
            }
        } else if (level < currentLevel) {
            for (var i = currentLevel; i > level; i--) {
                toc += "</ul></li>";
            }
        } else {
            toc += "</li>";
        }

        header.id = header.textContent.replace(/\s+/g, '-').toLowerCase(); // Create an ID for linking
        toc += "<li><a href='#" + header.id + "'>" + header.textContent + "</a>";
        currentLevel = level;
    });

    toc += "</li></ul></nav>";

    // Append the TOC to a specific element, e.g., a div with the ID 'toc-container'
    document.getElementById('toc-container').innerHTML = toc;
}

// Run the function when the document is fully loaded
document.addEventListener('DOMContentLoaded', generateTOC);