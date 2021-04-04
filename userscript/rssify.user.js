// ==UserScript==
// @name     rssify add
// @version  1
// @grant    none
// ==/UserScript==
document.addEventListener('keyup', async e => {
  if (e.key == "U" && e.ctrlKey) {
    fetch(
      "http://127.0.0.1:5000/add", 
      {headers: {"Content-Type": "application/json"}, 
       body: JSON.stringify({url: window.location.href}), 
       method:"POST"})
    .then(data => {return data.json();})
    .then(data => {
      console.log("Obtained link %s with added status %s and reason %s", data["link"], data["added"], data["reason"]);
      if (data["added"]) {
        alert("Rssified website. Link to RSS feed:\n" + data["link"]);
      } else {
        alert("Couldn't rssify website. Reason: " + data["reason"]);
      }
    });
  }
});