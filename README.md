# Back Benchers Food Stall

Online ordering with Razorpay payments.

Customers browse the menu, pay with Razorpay, and get an Order ID.
Orders show up on the admin page, where the stall moves them through
**Confirmed → Preparing → Ready → Completed**.

---

## 1. Run it on your computer

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # Windows  (Mac/Linux: cp .env.example .env)
```

Open `.env` and fill in:

| Setting | Where to get it |
|---|---|
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` | Razorpay Dashboard → Account & Settings → API Keys. Use **Test Mode** keys (`rzp_test_...`) first. |
| `ADMIN_PASSWORD` | Make one up. Needed to open `/admin`. |
| `DATABASE_URL` | Leave empty on your computer — it uses `database.db`. |

Then:

```bash
python app.py
```

- Website: http://localhost:5000
- Admin: http://localhost:5000/admin (username `admin`, your password)

In Test Mode, pay with Razorpay's test UPI ID `success@razorpay`
or the test cards listed in Razorpay's docs. No real money moves.

---

## 2. Put it online (Render)

### a) Make a database (free)

Render's free plan **erases files on every restart**, so `database.db`
can't be used online. Create a free Postgres database, for example on
[Neon](https://neon.tech), and copy its connection string
(`postgresql://...`).

### b) Create the web service

On Render: **New → Web Service** → connect the GitHub repo.

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`

### c) Add Environment Variables (Render → your service → Environment)

```
RAZORPAY_KEY_ID          = rzp_test_... (later rzp_live_...)
RAZORPAY_KEY_SECRET      = ...
RAZORPAY_WEBHOOK_SECRET  = any long random text
ADMIN_USERNAME           = admin
ADMIN_PASSWORD           = a strong password
DATABASE_URL             = postgresql://...  (from step a)
```

### d) Add the Razorpay webhook

Razorpay Dashboard → **Webhooks → Add New Webhook**

- **URL:** `https://<your-render-site>.onrender.com/razorpay-webhook`
- **Secret:** the same text as `RAZORPAY_WEBHOOK_SECRET`
- **Event:** tick `order.paid`

This confirms orders even if a customer closes their phone browser
right after paying.

### e) Check it

Open `https://<your-site>/health`. You should see
`"razorpay": true`, `"database": "postgres"`, `"adminLocked": false`.

Then place one test order and check it appears on `/admin`.

### f) Go live

When everything works in Test Mode, generate **Live** keys in Razorpay,
replace `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` on Render, and add the
webhook again in Live Mode (Test and Live webhooks are separate).

---

## Changing the menu

**Prices live in one place only: `MENU` in `app.py`.**
The menu page, cart and payment all read from it.

- **Change a price:** edit the number in `MENU`. Done.
- **Add a product:** add it to `MENU`, and add a card in
  `templates/menu.html` whose button has
  `data-product="<exactly the same name>"`. Show its price with
  `{{ price("<name>") }}`.
- **Product with dropdowns** (like size/flavour): also add it to
  `PRODUCT_CHOICES` at the top of `static/js/script.js`.

---

## Refunds and cancellations

"Cancel order" on the admin page only changes the order's status.
To give money back, refund the payment in the Razorpay Dashboard
(search by the Razorpay Payment ID shown on the order).

---

## Files

```
app.py               server: menu prices, payments, orders, admin
templates/           pages (menu, cart, checkout, success, admin)
static/js/script.js  menu + cart behaviour in the browser
.env.example         list of settings (copy to .env)
```

Never upload `.env` to GitHub — it contains your secret keys.
`.gitignore` already blocks it.
