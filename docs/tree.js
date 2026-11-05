/* Offline enhancement of the statically rendered JSON feature tree. */
(() => {
  "use strict";
  const features = [...document.querySelectorAll(".feature")];
  const branches = [...document.querySelectorAll(".branch")];
  const search = document.getElementById("search");
  const status = document.getElementById("matches");
  const empty = document.getElementById("empty");
  const data = JSON.parse(document.getElementById("project-tree-data").textContent);
  document.getElementById("json-view").textContent = JSON.stringify(data, null, 2);

  function filter() {
    const terms = search.value.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
    let count = 0;
    features.forEach(feature => {
      const haystack = feature.dataset.search.toLocaleLowerCase();
      feature.hidden = !terms.every(term => haystack.includes(term));
      if (!feature.hidden) {
        count++;
        if (terms.length) feature.querySelectorAll("details").forEach(item => { item.open = true; });
      }
    });
    branches.forEach(branch => {
      branch.hidden = ![...branch.querySelectorAll(".feature")].some(item => !item.hidden);
      if (terms.length && !branch.hidden) branch.querySelector("details").open = true;
    });
    empty.hidden = count !== 0;
    status.textContent = `${count} of ${features.length} guides${terms.length ? " match" : " · browse or search"}`;
  }
  search.addEventListener("input", filter);
  for (const [id, open] of [["expand", true], ["collapse", false]]) {
    document.getElementById(id).addEventListener("click", () => {
      document.querySelectorAll("#tree details").forEach(item => { item.open = open; });
    });
  }
  filter();
})();
