// ============================================================
// PRICES
//
// Prices come from MENU in app.py (the page sets
// window.MENU_PRICES). Do NOT write prices in this file.
// ============================================================

const MENU_PRICES = window.MENU_PRICES || {};

const MAX_QUANTITY = window.MAX_QUANTITY || 20;

function priceOf(product, option, size) {
  const choices = MENU_PRICES[product];

  if (!choices) return undefined;

  return choices[(option || "") + "|" + (size || "")];
}

// ============================================================
// PRODUCT CHOICES
//
// Which dropdowns belong to which product, and where its
// price is shown. Products without dropdowns aren't listed.
// ============================================================

const PRODUCT_CHOICES = {
  "Chips Mix Loaded": {
    option: "chips-type",
    size: "chips-size",
    price: "chips-price",
  },

  "Masaka Bun": {
    option: "bun-flavour",
    price: "bun-price",
  },

  "Veg Loaded French Fries": {
    size: "veg-fries-size",
    price: "veg-fries-price",
  },

  "Non Veg Loaded French Fries": {
    size: "nonveg-fries-size",
    price: "nonveg-fries-price",
  },

  Golisoda: {
    option: "golisoda-flavour",
    price: "golisoda-price",
  },

  "Back Benchers Burger": {
    option: "burger-type",
    size: "burger-size",
    price: "burger-price",
  },
};

function selectedValue(elementId) {
  const element = elementId ? document.getElementById(elementId) : null;

  return element ? element.value : "";
}

function selectedChoices(product) {
  const choices = PRODUCT_CHOICES[product] || {};

  return {
    option: selectedValue(choices.option),
    size: selectedValue(choices.size),
  };
}

// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHTML(value) {
  return String(value === null || value === undefined ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ============================================================
// CART STORAGE
// ============================================================

function getCart() {
  try {
    const cart = JSON.parse(localStorage.getItem("cart"));

    return Array.isArray(cart) ? cart : [];
  } catch (error) {
    return [];
  }
}

function saveCart(cart) {
  localStorage.setItem("cart", JSON.stringify(cart));
}

document.addEventListener("DOMContentLoaded", function () {
  // ==========================================================
  // LIVE PRICE UPDATE WHEN A DROPDOWN CHANGES
  // ==========================================================

  Object.keys(PRODUCT_CHOICES).forEach(function (product) {
    const choices = PRODUCT_CHOICES[product];

    const priceElement = document.getElementById(choices.price);

    if (!priceElement) return;

    function updatePrice() {
      const selected = selectedChoices(product);

      const price = priceOf(product, selected.option, selected.size);

      priceElement.textContent = price === undefined ? "—" : "₹" + price;
    }

    [choices.option, choices.size].forEach(function (elementId) {
      const element = elementId ? document.getElementById(elementId) : null;

      if (element) {
        element.addEventListener("change", updatePrice);
      }
    });

    updatePrice();
  });

  // ==========================================================
  // ADD TO CART
  // ==========================================================

  document.querySelectorAll(".add-cart-btn").forEach(function (button) {
    button.addEventListener("click", function () {
      const product = (button.dataset.product || "").trim();

      if (!product) {
        alert("Product name not found!");

        return;
      }

      const selected = selectedChoices(product);

      const price = priceOf(product, selected.option, selected.size);

      if (price === undefined) {
        alert("Price not available!");

        return;
      }

      // IMAGE

      const card =
        button.closest(".food-card") ||
        button.closest(".combo-card") ||
        button.closest(".food-category");

      const imageElement = card ? card.querySelector("img") : null;

      const image = imageElement ? imageElement.getAttribute("src") || "" : "";

      // SAME ITEM ALREADY IN CART -> INCREASE QUANTITY

      const cart = getCart();

      const existingItem = cart.find(function (cartItem) {
        return (
          cartItem.name === product &&
          (cartItem.option || "") === selected.option &&
          (cartItem.size || "") === selected.size
        );
      });

      if (existingItem) {
        if (Number(existingItem.quantity || 1) >= MAX_QUANTITY) {
          alert("You can order at most " + MAX_QUANTITY + " of one item.");

          return;
        }

        existingItem.quantity = Number(existingItem.quantity || 1) + 1;

        existingItem.price = price;
      } else {
        cart.push({
          name: product,
          option: selected.option,
          size: selected.size,
          price: price,
          quantity: 1,
          image: image,
        });
      }

      saveCart(cart);

      alert(product + " added to cart! 🛒");
    });
  });

  // ==========================================================
  // CART PAGE
  // ==========================================================

  if (document.getElementById("cart-items")) {
    loadCart();
  }
});

// ============================================================
// LOAD CART
//
// Re-checks every item against the current prices, so an
// old cart never shows an outdated price.
// ============================================================

function loadCart() {
  let cart = getCart();

  if (Object.keys(MENU_PRICES).length > 0) {
    const removed = [];

    cart = cart.filter(function (item) {
      const price = priceOf(item.name, item.option, item.size);

      if (price === undefined) {
        removed.push(item.name);

        return false;
      }

      item.price = price;

      item.quantity = Math.min(
        Math.max(parseInt(item.quantity, 10) || 1, 1),
        MAX_QUANTITY,
      );

      return true;
    });

    saveCart(cart);

    if (removed.length > 0) {
      alert(
        "These items are no longer on the menu and were removed from your cart:\n\n" +
          removed.join("\n"),
      );
    }
  }

  saveCartAndRender(cart);
}

// ============================================================
// RENDER CART
// ============================================================

function renderCart(cart) {
  const cartContainer = document.getElementById("cart-items");

  const cartTotal = document.getElementById("cart-total");

  if (!cartContainer) return;

  cartContainer.innerHTML = "";

  let total = 0;

  cart.forEach(function (item, index) {
    const quantity = Number(item.quantity || 1);

    const price = Number(item.price || 0);

    const itemTotal = price * quantity;

    total += itemTotal;

    const cartItem = document.createElement("div");

    cartItem.className = "cart-item";

    const imageHTML = item.image
      ? `
        <div class="cart-item-image">
          <img
            src="${escapeHTML(item.image)}"
            alt="${escapeHTML(item.name)}"
          >
        </div>
      `
      : "";

    cartItem.innerHTML = `

      ${imageHTML}

      <div class="cart-item-info">

        <h3>
          ${escapeHTML(item.name)}
        </h3>

        ${item.option ? `<p>${escapeHTML(item.option)}</p>` : ""}

        ${item.size ? `<p>Size: ${escapeHTML(item.size)}</p>` : ""}

        <strong>
          ₹${price}
        </strong>

      </div>


      <div class="cart-item-actions">

        <div class="quantity-control">

          <button
            class="quantity-btn minus-btn"
            data-index="${index}"
          >
            −
          </button>

          <span class="quantity">
            ${quantity}
          </span>

          <button
            class="quantity-btn plus-btn"
            data-index="${index}"
          >
            +
          </button>

        </div>


        <strong class="item-total">
          ₹${itemTotal}
        </strong>


        <button
          class="remove-btn"
          data-index="${index}"
        >
          Remove
        </button>

      </div>

    `;

    cartContainer.appendChild(cartItem);
  });

  if (cartTotal) {
    cartTotal.textContent = "₹" + total;
  }

  // PLUS

  document.querySelectorAll(".plus-btn").forEach(function (button) {
    button.addEventListener("click", function () {
      const index = Number(button.dataset.index);

      if (Number(cart[index].quantity || 1) >= MAX_QUANTITY) {
        alert("You can order at most " + MAX_QUANTITY + " of one item.");

        return;
      }

      cart[index].quantity = Number(cart[index].quantity || 1) + 1;

      saveCartAndRender(cart);
    });
  });

  // MINUS

  document.querySelectorAll(".minus-btn").forEach(function (button) {
    button.addEventListener("click", function () {
      const index = Number(button.dataset.index);

      cart[index].quantity = Number(cart[index].quantity || 1) - 1;

      if (cart[index].quantity <= 0) {
        cart.splice(index, 1);
      }

      saveCartAndRender(cart);
    });
  });

  // REMOVE

  document.querySelectorAll(".remove-btn").forEach(function (button) {
    button.addEventListener("click", function () {
      const index = Number(button.dataset.index);

      cart.splice(index, 1);

      saveCartAndRender(cart);
    });
  });
}

// ============================================================
// SAVE + RENDER (also handles the empty cart)
// ============================================================

function saveCartAndRender(cart) {
  saveCart(cart);

  const cartContainer = document.getElementById("cart-items");

  const emptyCart = document.getElementById("empty-cart");

  const cartContent = document.getElementById("cart-content");

  const isEmpty = cart.length === 0;

  if (emptyCart) {
    emptyCart.style.display = isEmpty ? "block" : "none";
  }

  if (cartContent) {
    cartContent.style.display = isEmpty ? "none" : "block";
  }

  if (isEmpty) {
    if (cartContainer) {
      cartContainer.innerHTML = "";
    }

    return;
  }

  renderCart(cart);
}
