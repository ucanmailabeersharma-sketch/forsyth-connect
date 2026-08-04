/* =========================================================
   FORSYTH CONNECT — script.js
   This file does three jobs:
   1. Store the list of community resources (the "data")
   2. Build the filter buttons and resource cards from that data
   3. Handle searching, filtering, and the detail popup
   ========================================================= */

// -----------------------------------------------------------
// 1. THE DATA
// -----------------------------------------------------------
// IMPORTANT: These are PLACEHOLDER entries so the app runs and
// looks right. Before submitting, replace these with REAL
// Forsyth County resources you research yourself — real names,
// addresses, phone numbers, and hours. Judges may check these,
// and using real data is a big part of what makes this project
// legitimate rather than just a demo.
//
// To add a new resource, copy one of these objects and change
// the values. "category" must match one of the categories used
// below (Food, Health, Housing, Education) or add a new one —
// the filter buttons are generated automatically from whatever
// categories appear here, so you don't have to update the HTML.

const resources = [
  {
    id: 1,
    name: "Forsyth County Food Pantry",
    category: "Food",
    description: "Free groceries and shelf-stable food for families in need, no appointment required.",
    address: "REPLACE WITH REAL ADDRESS",
    phone: "REPLACE WITH REAL PHONE NUMBER",
    hours: "REPLACE WITH REAL HOURS"
  },
  {
    id: 2,
    name: "Community Free Clinic",
    category: "Health",
    description: "Free basic health screenings and referrals for uninsured residents.",
    address: "REPLACE WITH REAL ADDRESS",
    phone: "REPLACE WITH REAL PHONE NUMBER",
    hours: "REPLACE WITH REAL HOURS"
  },
  {
    id: 3,
    name: "After-School Tutoring Program",
    category: "Education",
    description: "Free peer and volunteer-led tutoring for K-12 students in core subjects.",
    address: "REPLACE WITH REAL ADDRESS",
    phone: "REPLACE WITH REAL PHONE NUMBER",
    hours: "REPLACE WITH REAL HOURS"
  },
  {
    id: 4,
    name: "Housing Assistance Center",
    category: "Housing",
    description: "Guidance and emergency support for families facing eviction or housing insecurity.",
    address: "REPLACE WITH REAL ADDRESS",
    phone: "REPLACE WITH REAL PHONE NUMBER",
    hours: "REPLACE WITH REAL HOURS"
  },
  {
    id: 5,
    name: "Mobile Food Distribution",
    category: "Food",
    description: "Weekly mobile food truck bringing fresh produce to underserved neighborhoods.",
    address: "REPLACE WITH REAL ADDRESS",
    phone: "REPLACE WITH REAL PHONE NUMBER",
    hours: "REPLACE WITH REAL HOURS"
  },
  {
    id: 6,
    name: "Youth Mental Health Support",
    category: "Health",
    description: "Free and low-cost counseling services for teens and families.",
    address: "REPLACE WITH REAL ADDRESS",
    phone: "REPLACE WITH REAL PHONE NUMBER",
    hours: "REPLACE WITH REAL HOURS"
  }
];

// This keeps track of which category filter is currently selected.
// "All" means no filter is applied.
let activeCategory = "All";

// -----------------------------------------------------------
// 2. GRAB THE HTML ELEMENTS WE NEED TO UPDATE
// -----------------------------------------------------------
const searchInput = document.getElementById("searchInput");
const filterChips = document.getElementById("filterChips");
const resourceGrid = document.getElementById("resourceGrid");
const resultsCount = document.getElementById("resultsCount");
const emptyState = document.getElementById("emptyState");

const modalOverlay = document.getElementById("modalOverlay");
const modalClose = document.getElementById("modalClose");
const modalCategory = document.getElementById("modalCategory");
const modalTitle = document.getElementById("modalTitle");
const modalDescription = document.getElementById("modalDescription");
const modalAddress = document.getElementById("modalAddress");
const modalPhone = document.getElementById("modalPhone");
const modalHours = document.getElementById("modalHours");

// -----------------------------------------------------------
// 3. BUILD THE FILTER CHIPS (buttons like "All", "Food", "Health"...)
// -----------------------------------------------------------
function buildFilterChips() {
  // Get every unique category from the data, e.g. ["Food", "Health", "Education", "Housing"]
  const categories = ["All", ...new Set(resources.map(r => r.category))];

  filterChips.innerHTML = "";

  categories.forEach(category => {
    const button = document.createElement("button");
    button.className = "chip" + (category === activeCategory ? " active" : "");
    button.textContent = category;
    button.addEventListener("click", () => {
      activeCategory = category;
      buildFilterChips(); // redraw chips so the "active" style moves
      renderResources();  // redraw the grid with the new filter applied
    });
    filterChips.appendChild(button);
  });
}

// -----------------------------------------------------------
// 4. FILTER + SEARCH LOGIC
// -----------------------------------------------------------
function getFilteredResources() {
  const query = searchInput.value.trim().toLowerCase();

  return resources.filter(r => {
    const matchesCategory = activeCategory === "All" || r.category === activeCategory;
    const matchesSearch =
      query === "" ||
      r.name.toLowerCase().includes(query) ||
      r.description.toLowerCase().includes(query) ||
      r.category.toLowerCase().includes(query);

    return matchesCategory && matchesSearch;
  });
}

// -----------------------------------------------------------
// 5. RENDER THE RESOURCE CARDS
// -----------------------------------------------------------
function renderResources() {
  const filtered = getFilteredResources();

  resourceGrid.innerHTML = "";

  // Update the "Showing X resources" text
  resultsCount.textContent = `Showing ${filtered.length} of ${resources.length} resources`;

  // Show/hide the "no results" message
  emptyState.hidden = filtered.length !== 0;

  filtered.forEach(resource => {
    const card = document.createElement("button");
    card.className = "resource-card";
    card.innerHTML = `
      <span class="card-category">${resource.category}</span>
      <h3 class="card-title">${resource.name}</h3>
      <p class="card-desc">${resource.description}</p>
    `;
    card.addEventListener("click", () => openModal(resource));
    resourceGrid.appendChild(card);
  });
}

// -----------------------------------------------------------
// 6. MODAL (the popup that shows full details for one resource)
// -----------------------------------------------------------
function openModal(resource) {
  modalCategory.textContent = resource.category;
  modalTitle.textContent = resource.name;
  modalDescription.textContent = resource.description;
  modalAddress.textContent = resource.address;
  modalPhone.textContent = resource.phone;
  modalHours.textContent = resource.hours;
  modalOverlay.hidden = false;
}

function closeModal() {
  modalOverlay.hidden = true;
}

modalClose.addEventListener("click", closeModal);

// Clicking the dark overlay (outside the white box) also closes it
modalOverlay.addEventListener("click", (event) => {
  if (event.target === modalOverlay) closeModal();
});

// Pressing Escape also closes it
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeModal();
});

// -----------------------------------------------------------
// 7. SEARCH INPUT — re-render every time the user types
// -----------------------------------------------------------
searchInput.addEventListener("input", renderResources);

// -----------------------------------------------------------
// 8. INITIAL SETUP — run once when the page loads
// -----------------------------------------------------------
buildFilterChips();
renderResources();
