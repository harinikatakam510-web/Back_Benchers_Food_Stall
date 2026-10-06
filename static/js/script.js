document.addEventListener("DOMContentLoaded", function () {
  // ==========================================================
  // PRICE FUNCTIONS
  // ==========================================================

  // ==========================================================
  // 1. CHIPS MIX LOADED
  // ==========================================================

  const chipsType = document.getElementById("chips-type");
  const chipsSize = document.getElementById("chips-size");
  const chipsPrice = document.getElementById("chips-price");

  function updateChipsPrice() {
    if (!chipsType || !chipsSize || !chipsPrice) return;

    let price;

    if (chipsType.value === "Veg Loaded") {
      price = chipsSize.value === "Mini" ? 49 : 69;
    } else {
      price = chipsSize.value === "Mini" ? 59 : 79;
    }

    chipsPrice.textContent = "₹" + price;
  }

  if (chipsType) {
    chipsType.addEventListener("change", updateChipsPrice);
  }

  if (chipsSize) {
    chipsSize.addEventListener("change", updateChipsPrice);
  }

  updateChipsPrice();

  // ==========================================================
  // 2. MASAKA BUN
  // ==========================================================

  const bunFlavour = document.getElementById("bun-flavour");
  const bunPrice = document.getElementById("bun-price");

  function updateBunPrice() {
    if (!bunFlavour || !bunPrice) return;

    if (bunFlavour.value === "Mixed Flavour Bun") {
      bunPrice.textContent = "₹69";
    } else {
      bunPrice.textContent = "₹49";
    }
  }

  if (bunFlavour) {
    bunFlavour.addEventListener("change", updateBunPrice);
  }

  updateBunPrice();

  // ==========================================================
  // 3. VEG FRIES
  // ==========================================================

  const vegFriesSize = document.getElementById("veg-fries-size");
  const vegFriesPrice = document.getElementById("veg-fries-price");

  function updateVegFriesPrice() {
    if (!vegFriesSize || !vegFriesPrice) return;

    vegFriesPrice.textContent = vegFriesSize.value === "Mini" ? "₹59" : "₹89";
  }

  if (vegFriesSize) {
    vegFriesSize.addEventListener("change", updateVegFriesPrice);
  }

  updateVegFriesPrice();

  // ==========================================================
  // 4. NON VEG FRIES
  // ==========================================================

  const nonVegFriesSize = document.getElementById("nonveg-fries-size");

  const nonVegFriesPrice = document.getElementById("nonveg-fries-price");

  function updateNonVegFriesPrice() {
    if (!nonVegFriesSize || !nonVegFriesPrice) return;

    nonVegFriesPrice.textContent =
      nonVegFriesSize.value === "Mini" ? "₹69" : "₹99";
  }

  if (nonVegFriesSize) {
    nonVegFriesSize.addEventListener("change", updateNonVegFriesPrice);
  }

  updateNonVegFriesPrice();

  // ==========================================================
  // 5. GOLISODA
  // ==========================================================

  const golisodaFlavour = document.getElementById("golisoda-flavour");

  const golisodaPrice = document.getElementById("golisoda-price");

  function updateGolisodaPrice() {
    if (!golisodaPrice) return;

    // Change this amount if your actual Golisoda price is different
    golisodaPrice.textContent = "₹30";
  }

  if (golisodaFlavour) {
    golisodaFlavour.addEventListener("change", updateGolisodaPrice);
  }

  updateGolisodaPrice();

  // ==========================================================
  // 6. BURGER
  // ==========================================================

  const burgerType = document.getElementById("burger-type");

  const burgerSize = document.getElementById("burger-size");

  const burgerPrice = document.getElementById("burger-price");

  function updateBurgerPrice() {
    if (!burgerType || !burgerSize || !burgerPrice) return;

    let price;

    if (burgerType.value === "Veg Burger") {
      price = burgerSize.value === "Mini" ? 49 : 69;
    } else {
      price = burgerSize.value === "Mini" ? 59 : 89;
    }

    burgerPrice.textContent = "₹" + price;
  }

  if (burgerType) {
    burgerType.addEventListener("change", updateBurgerPrice);
  }

  if (burgerSize) {
    burgerSize.addEventListener("change", updateBurgerPrice);
  }

  updateBurgerPrice();

  // ==========================================================
  // NEW MENU ITEMS
  // ==========================================================

  // ==========================================================
  // 7. BANGALORE SPECIAL SWEET
  // ==========================================================

  const bangalorePrice = document.getElementById("bangalore-price");

  if (bangalorePrice) {
    bangalorePrice.textContent = "₹49";
  }

  // ==========================================================
  // 8. BLACK FOREST
  // ==========================================================

  const blackForestPrice = document.getElementById("black-forest-price");

  if (blackForestPrice) {
    blackForestPrice.textContent = "₹89";
  }

  // ==========================================================
  // 9. KAJU CHICKEN FRY
  // ==========================================================

  const kajuChickenPrice = document.getElementById("kaju-chicken-price");

  if (kajuChickenPrice) {
    kajuChickenPrice.textContent = "₹99";
  }

  // ==========================================================
  // 10. CHOCOLATE CAKE
  // ==========================================================

  const chocolateCakePrice = document.getElementById("chocolate-cake-price");

  if (chocolateCakePrice) {
    chocolateCakePrice.textContent = "₹89";
  }

  // ==========================================================
  // 11. SOFT DRINK
  // ==========================================================

  const softDrinkPrice = document.getElementById("soft-drink-price");

  if (softDrinkPrice) {
    softDrinkPrice.textContent = "₹15";
  }

  // ==========================================================
  // 12. SAMOSA
  // ==========================================================

  const samosaPrice = document.getElementById("samosa-price");

  if (samosaPrice) {
    samosaPrice.textContent = "₹15";
  }

  // ==========================================================
  // COMBO PRICE DISPLAY
  // ==========================================================

  const comboPrices = {
    "Drink + Samosa (Combo)": 25,

    "Chocolate Cake / Black Forest + Samosa + Soft Drink (Combo)": 149,

    "Kaju Chicken Fry + Drink + Chaco Chaco (Combo)": 179,
  };

  Object.keys(comboPrices).forEach(function (comboName) {
    const safeId = comboName
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");

    const priceElement = document.getElementById(safeId + "-price");

    if (priceElement) {
      priceElement.textContent = "₹" + comboPrices[comboName];
    }
  });

  // ==========================================================
  // ADD TO CART
  // ==========================================================

  const cartButtons = document.querySelectorAll(".add-cart-btn");

  cartButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const foodInfo = button.closest(".food-info");

      /*
       * Combo cards may not have .food-info
       * because combo design is different.
       *
       * So first try food-info,
       * otherwise use closest food-card.
       */

      const card =
        button.closest(".food-card") ||
        button.closest(".combo-card") ||
        button.closest(".food-category");

      // ======================================================
      // PRODUCT NAME
      // ======================================================

      let product = "";

      if (button.dataset.product) {
        product = button.dataset.product.trim();
      } else if (foodInfo) {
        const heading = foodInfo.querySelector("h3");

        if (heading) {
          product = heading.textContent.trim();
        }
      } else if (card) {
        const heading = card.querySelector("h2, h3");

        if (heading) {
          product = heading.textContent.trim();
        }
      }

      if (!product) {
        alert("Product name not found!");

        return;
      }

      // ======================================================
      // GET IMAGE
      // ======================================================

      let image = "";

      const imageElement = card ? card.querySelector("img") : null;

      if (imageElement) {
        image = imageElement.getAttribute("src") || "";
      }

      // If button has image path
      if (button.dataset.image) {
        image = button.dataset.image;
      }

      // ======================================================
      // CREATE ITEM
      // ======================================================

      let item = {
        name: product,

        option: "",

        size: "",

        price: 0,

        quantity: 1,

        image: image,
      };

      // ======================================================
      // CHIPS
      // ======================================================

      if (product === "Chips Mix Loaded") {
        if (chipsType && chipsSize) {
          item.option = chipsType.value;

          item.size = chipsSize.value;

          if (chipsType.value === "Veg Loaded") {
            item.price = chipsSize.value === "Mini" ? 49 : 69;
          } else {
            item.price = chipsSize.value === "Mini" ? 59 : 79;
          }
        }
      }

      // ======================================================
      // MASAKA BUN
      // ======================================================
      else if (product === "Masaka Bun") {
        if (bunFlavour) {
          item.option = bunFlavour.value;

          item.price = bunFlavour.value === "Mixed Flavour Bun" ? 69 : 49;
        }
      }

      // ======================================================
      // VEG FRIES
      // ======================================================
      else if (product === "Veg Loaded French Fries") {
        if (vegFriesSize) {
          item.size = vegFriesSize.value;

          item.price = vegFriesSize.value === "Mini" ? 59 : 89;
        }
      }

      // ======================================================
      // NON VEG FRIES
      // ======================================================
      else if (product === "Non Veg Loaded French Fries") {
        if (nonVegFriesSize) {
          item.size = nonVegFriesSize.value;

          item.price = nonVegFriesSize.value === "Mini" ? 69 : 99;
        }
      }

      // ======================================================
      // GOLISODA
      // ======================================================
      else if (product === "Golisoda") {
        const flavour = document.getElementById("golisoda-flavour");

        item.option = flavour ? flavour.value : "";

        item.price = 30;
      }

      // ======================================================
      // BURGER
      // ======================================================
      else if (product === "Back Benchers Burger") {
        if (burgerType && burgerSize) {
          item.option = burgerType.value;

          item.size = burgerSize.value;

          if (burgerType.value === "Veg Burger") {
            item.price = burgerSize.value === "Mini" ? 49 : 69;
          } else {
            item.price = burgerSize.value === "Mini" ? 59 : 89;
          }
        }
      }

      // ======================================================
      // BANGALORE SPECIAL SWEET
      // ======================================================
      else if (product === "Bangalore Special Sweet") {
        item.price = 49;
      }

      // ======================================================
      // BLACK FOREST
      // ======================================================
      else if (product === "Black Forest") {
        item.price = 89;
      }

      // ======================================================
      // KAJU CHICKEN FRY
      // ======================================================
      else if (product === "Kaju Chicken Fry") {
        item.price = 99;
      }

      // ======================================================
      // CHOCOLATE CAKE
      // ======================================================
      else if (product === "Chocolate Cake") {
        item.price = 89;
      }

      // ======================================================
      // SOFT DRINK
      // ======================================================
      else if (product === "Soft Drink") {
        item.price = 15;
      }

      // ======================================================
      // SAMOSA
      // ======================================================
      else if (product === "Samosa") {
        item.price = 15;
      }

      // ======================================================
      // COMBO 1
      // ======================================================
      else if (product === "Drink + Samosa (Combo)") {
        item.price = 25;

        item.option = "Soft Drink + Samosa";
      }

      // ======================================================
      // COMBO 2
      // ======================================================
      else if (
        product ===
        "Chocolate Cake / Black Forest + Samosa + Soft Drink (Combo)"
      ) {
        item.price = 149;

        item.option = "Any Cake + Samosa + Soft Drink";
      }

      // ======================================================
      // COMBO 3
      // ======================================================
      else if (product === "Kaju Chicken Fry + Drink + Chaco Chaco (Combo)") {
        item.price = 179;

        item.option = "Kaju Chicken Fry + Soft Drink + Chaco Chaco";
      }

      // ======================================================
      // DATA-BASED COMBO SUPPORT
      // ======================================================

      /*
       * If you give a combo button:
       *
       * data-combo="true"
       * data-price="149"
       *
       * then price is automatically taken.
       */

      if (button.dataset.combo === "true") {
        const comboPrice = Number(button.dataset.price);

        if (comboPrice && comboPrice > 0) {
          item.price = comboPrice;
        }
      }

      // ======================================================
      // DATA PRICE SUPPORT
      // ======================================================

      if (button.dataset.price && Number(button.dataset.price) > 0) {
        item.price = Number(button.dataset.price);
      }

      // ======================================================
      // CHECK PRICE
      // ======================================================

      if (!item.price || item.price <= 0) {
        alert("Price not available!");

        return;
      }

      // ======================================================
      // GET EXISTING CART
      // ======================================================

      let cart = [];

      try {
        cart = JSON.parse(localStorage.getItem("cart")) || [];
      } catch (error) {
        cart = [];
      }

      // ======================================================
      // CHECK SAME ITEM
      // ======================================================

      const existingItem = cart.find(function (cartItem) {
        return (
          cartItem.name === item.name &&
          cartItem.option === item.option &&
          cartItem.size === item.size
        );
      });

      // ======================================================
      // QUANTITY
      // ======================================================

      if (existingItem) {
        existingItem.quantity = Number(existingItem.quantity || 1) + 1;
      } else {
        cart.push(item);
      }

      // ======================================================
      // SAVE CART
      // ======================================================

      localStorage.setItem("cart", JSON.stringify(cart));

      // ======================================================
      // SUCCESS MESSAGE
      // ======================================================

      alert(item.name + " added to cart! 🛒");
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
// ============================================================

function loadCart() {
  const cartContainer = document.getElementById("cart-items");

  const emptyCart = document.getElementById("empty-cart");

  const cartContent = document.getElementById("cart-content");

  if (!cartContainer) return;

  let cart = [];

  try {
    cart = JSON.parse(localStorage.getItem("cart")) || [];
  } catch (error) {
    cart = [];
  }

  // ==========================================================
  // EMPTY CART
  // ==========================================================

  if (cart.length === 0) {
    cartContainer.innerHTML = "";

    if (emptyCart) {
      emptyCart.style.display = "block";
    }

    if (cartContent) {
      cartContent.style.display = "none";
    }

    return;
  }

  // ==========================================================
  // SHOW CART
  // ==========================================================

  if (emptyCart) {
    emptyCart.style.display = "none";
  }

  if (cartContent) {
    cartContent.style.display = "block";
  }

  renderCart(cart);
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

    // ========================================================
    // IMAGE HTML
    // ========================================================

    let imageHTML = "";

    if (item.image) {
      imageHTML = `
        <div class="cart-item-image">
          <img
            src="${item.image}"
            alt="${item.name}"
          >
        </div>
      `;
    }

    // ========================================================
    // CART ITEM HTML
    // ========================================================

    cartItem.innerHTML = `

      ${imageHTML}

      <div class="cart-item-info">

        <h3>
          ${item.name}
        </h3>

        ${item.option ? `<p>${item.option}</p>` : ""}

        ${item.size ? `<p>Size: ${item.size}</p>` : ""}

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

  // ==========================================================
  // TOTAL
  // ==========================================================

  if (cartTotal) {
    cartTotal.textContent = "₹" + total;
  }

  // ==========================================================
  // PLUS BUTTON
  // ==========================================================

  document.querySelectorAll(".plus-btn").forEach(function (button) {
    button.addEventListener("click", function () {
      const index = Number(button.dataset.index);

      cart[index].quantity = Number(cart[index].quantity || 1) + 1;

      saveCartAndRender(cart);
    });
  });

  // ==========================================================
  // MINUS BUTTON
  // ==========================================================

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

  // ==========================================================
  // REMOVE
  // ==========================================================

  document.querySelectorAll(".remove-btn").forEach(function (button) {
    button.addEventListener("click", function () {
      const index = Number(button.dataset.index);

      cart.splice(index, 1);

      saveCartAndRender(cart);
    });
  });
}

// ============================================================
// SAVE + RENDER
// ============================================================

function saveCartAndRender(cart) {
  localStorage.setItem("cart", JSON.stringify(cart));

  if (cart.length === 0) {
    const cartContainer = document.getElementById("cart-items");

    const emptyCart = document.getElementById("empty-cart");

    const cartContent = document.getElementById("cart-content");

    if (cartContainer) {
      cartContainer.innerHTML = "";
    }

    if (emptyCart) {
      emptyCart.style.display = "block";
    }

    if (cartContent) {
      cartContent.style.display = "none";
    }

    return;
  }

  renderCart(cart);
}
