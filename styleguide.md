# **Brand & UI Guidelines: NHyeS**

## **1. Introduction**

### **Our Mission**
To provide users with clear, reliable, and accessible health information and services through the NHyeS app, upholding the core values of the NHS: trust, empathy, and care for all.

### **Core Principles**
Our design and communication are guided by three principles:

1.  **Accessibility First:** We are designing for everyone, regardless of ability, technical confidence, or context. Our app must meet or exceed **WCAG 2.1 AA** standards.
2.  **Clarity & Simplicity:** We use simple language and intuitive design. We avoid jargon and complexity, ensuring users can find what they need and understand it easily.
3.  **Trust & Reliability:** Our app must feel professional, secure, and supportive. Every design choice should build user confidence.

---

## **2. Brand Identity**

### **Logo**

* **App Name:** **NHyeS**
* **Logo Design:** As specified, the logo is a direct modification of the official NHS logotype. It replaces the 'NHS' text with 'NHyeS' while retaining the identical NHS-blue lozenge shape, proprietary typeface style, and colour.
* **Usage:** This logo is to be used as the primary identifier for the **NHyeS hackathon project** across all app screens, splash screens, and presentation materials.
* **Clear Space:** A minimum of 25% of the logo's height must be maintained as clear space on all sides.

### **Colour Palette**

Our palette is built from the official NHS digital colours to create an instant feeling of familiarity and trust.

#### **Primary Colours**
Used for primary calls-to-action, links, and navigation elements.

* **NHS Blue**
    * `#005EB8`
    * Use for the logo, primary buttons, active states, and links.
* **White**
    * `#FFFFFF`
    * Use for backgrounds and text on dark backgrounds.

#### **Secondary Colours**
Used for text, backgrounds, and structural elements.

* **Dark Blue**
    * `#003087`
    * Use for headings or secondary navigation.
* **Black**
    * `#212B32`
    * Use for all body text. Provides high contrast and is easier to read than 100% black.
* **NHS Light Grey**
    * `#F0F4F5`
    * Use for page backgrounds to reduce glare from pure white.
* **NHS Mid Grey**
    * `#AEB7B3`
    * Use for borders, dividers, and disabled form elements.

#### **System & Accent Colours**
Use these colours sparingly to communicate specific meanings.

* **Green (Success)**
    * `#007F3B`
    * Use for success messages and validation.
* **Red (Error / Urgent)**
    * `#DA291C`
    * Use for error messages, critical alerts, and destructive actions (e.g., "Delete").
* **Amber (Warning / Info)**
    * `#FFB81C`
    * Use for warnings, non-critical alerts, and focus states.

### **Typography**

Clarity and legibility are paramount. While the official NHS font ("Frutiger") is proprietary, **Inter** is an excellent, free, and highly accessible alternative for all app UI text.

* **Primary Typeface:** **Inter** (Available on Google Fonts)
* **Fallback:** **Arial, Helvetica, sans-serif**

#### **Type Scale (Example)**
* **H1 / Page Title:** Inter Bold, 32px
* **H2 / Section Title:** Inter Bold, 24px
* **H3 / Card Title:** Inter Bold, 19px
* **Body (Default):** Inter Regular, 16px (This should be the minimum for all descriptive text).
* **Body (Small):** Inter Regular, 14px (Use sparingly, e.g., for captions or helper text).

#### **Rules**
* **Line Height:** Set line height to approximately **1.5x** the font size for optimal readability.
* **Line Length:** Aim for 50-75 characters per line for body copy.
* **Contrast:** All text must pass WCAG AA (4.5:1 ratio). Our default Black (`#212B32`) on White (`#FFFFFF`) or Light Grey (`#F0F4F5`) meets this standard.

### **Tone of Voice**

Our voice should be calm, clear, and empathetic.

| Do | Don't |
| --- | --- |
| Use simple, plain English. | Use medical jargon or overly technical terms. |
| Be supportive and reassuring. | Be cold, clinical, or alarming. |
| Use "you" and "we" to be direct. | Be impersonal or passive. |
| Use active voice ("Take your medicine"). | Use passive voice ("Medicine should be taken"). |
| Give clear instructions. | Be vague or ambiguous. |

**Example:**
* **Don't:** "It is imperative that patients cease medication if adverse symptoms present."
* **Do:** "Stop taking this medicine if you feel unwell. You can report any side effects to us."

---

## **3. UI (User Interface) Document**

### **Layout & Grid**

* **Grid System:** Use an **8-point grid**. All spacing, margins, and padding should be in multiples of 8 (e.g., 8px, 16px, 24px, 32px).
* **Whitespace:** Be generous with whitespace. It reduces cognitive load and improves focus.
* **Layout:** Use a single-column layout for mobile. Content should be structured linearly and logically.

### **Iconography**

* **Style:** Use a simple, universally understood, outlined icon set. **Material Symbols (Outlined)** is a strong, free choice that pairs well with the Inter typeface.
* **Size:** Icons should be clear and legible. A **24x24px** bounding box is standard.
* **Accessibility:** All icons that convey meaning *must* be accompanied by a text label or a non-visual `aria-label` for screen readers.

### **Core Components**

#### **1. Buttons**

Buttons are for primary actions. All buttons must have a minimum touch target of **44x44px**.

* **Primary Button:**
    * **Use:** The main call-to-action on a page (e.g., "Submit," "Book appointment").
    * **Style:** Solid **NHS Blue (`#005EB8`)** background, **White (`#FFFFFF`)** text.
    * **Hover:** Slightly darker blue (`#004C99`).
    * **Focus:** Default style with a 3px **Amber (`#FFB81C`)** outline.

* **Secondary Button:**
    * **Use:** Secondary actions (e.g., "Cancel," "Go back").
    * **Style:** **White (`#FFFFFF`)** background, 2px **NHS Blue (`#005EB8`)** border, **NHS Blue** text.
    * **Hover:** Light blue (`#F0F4F5`) background.
    * **Focus:** Default style with a 3px **Amber (`#FFB81C`)** outline.

* **Destructive Button:**
    * **Use:** Actions that delete data or are irreversible (e.g., "Delete account").
    * **Style:** Solid **Red (`#DA291C`)** background, **White (`#FFFFFF`)** text.
    * **Hover:** Darker red (`#B92317`).
    * **Focus:** Default style with a 3px **Amber (`#FFB81C`)** outline.

* **Disabled Button:**
    * **Style:** Solid **Mid Grey (`#AEB7B3`)** background, **Black (`#212B32`)** text (with 50% opacity). Non-interactive.

#### **2. Form Fields (Inputs)**

* **Labels:** All fields must have a clear `<label>` in **Inter Bold, 19px** or **16px**, positioned *above* the input.
* **Helper Text:** Use 14px regular text below the input for extra guidance.
* **Default State:** 2px **Mid Grey (`#AEB7B3`)** border, white background.
* **Focused State:** 2px **NHS Blue (`#005EB8`)** border and a 3px **Amber (`#FFB81C`)** outer outline.
* **Error State:** 2px **Red (`#DA291C`)** border. An error message (in red text) must appear below the field.

#### **3. Cards**

Used to group related information into a single, digestible container.

* **Style:** White background (`#FFFFFF`), rounded corners (8px), and a subtle border (1px, `AEB7B3`) or a light box-shadow.
* **Content:** Must contain a clear heading (H3, **Inter Bold, 19px**).
* **Clickable Cards:** If the entire card is a link, it should have a hover state (e.g., the heading turns blue and/or the card lifts).

#### **4. Alerts & Banners**

Used to provide timely, contextual information.

* **Information (Blue):** For general guidance. **NHS Blue (`#005EB8`)** left border (4px) and a light grey (`#F0F4F5`) background.
* **Success (Green):** For confirmation. **Green (`#007F3B`)** left border (4px) and a light green background.
* **Warning (Amber):** For important, non-critical advice. **Amber (`#FFB81C`)** left border (4px) and a light amber background.
* **Error (Red):** For critical errors. **Red (`#DA291C`)** left border (4px) and a light red background.

---

## **4. Accessibility Checklist (WCAG 2.1 AA)**

This is a non-negotiable part of the design.

* **Colour Contrast:** All text must have a **4.5:1 ratio**. All UI elements (like button borders) must have a **3:1 ratio**.
* **Focus States:** Every single interactive element (link, button, input, tab) *must* have a clear, visible focus state. We use the 3px **Amber (`#FFB81C`)** outline.
* **Touch Targets:** All interactive elements must be at least **44x44px**.
* **Text:** Minimum body text size is 16px. Users must be able to zoom or resize text up to 200% without breaking the layout.
* **Images:** All meaningful images must have descriptive `alt` text. Decorative images should have `alt=""`.
* **Navigation:** All navigation must be logical and consistent. The app must be fully navigable using only a keyboard or screen reader.
* **Forms:** All form fields must be correctly labelled. Error messages must be clear and identify which field is at fault.

Here are the component and styling suggestions for your "NHyeS" Next.js hackathon project.

For a hackathon, your top priorities are **speed of development** and **meeting the core requirements**. The most important requirement for an NHS-themed app is **accessibility (A11y)**, followed by the specific theme.

Based on this, here is my top recommendation.

## Top Recommendation: Shadcn UI

This is the best choice for your project. It's not a traditional component library; it's a collection of reusable components built on **Radix UI** and styled with **Tailwind CSS**.

  * **Why it's perfect for your hackathon:**
      * **Best-in-Class Accessibility:** It uses Radix UI primitives, which are fully accessible (keyboard navigation, focus management, screen reader support) right out of the box. This is non-negotiable for an NHS theme.
      * **Incredible Speed:** You use a CLI to add components (like `Button`, `Dialog`, `Input`) directly into your project. You can then style them instantly with Tailwind.
      * **Total Theming Control:** It's *designed* to be themed. You aren't fighting a library's default styles (like Material-UI). You can implement your "NHyeS" brand guidelines in minutes.

-----

### How to Implement Your Styling

1.  **Install Tailwind CSS:** Follow the official guide for Next.js.
2.  **Install Shadcn UI:** Run its `init` command. It will set up your `tailwind.config.js` file.
3.  **Configure Your `tailwind.config.js`:** Open the `tailwind.config.js` file and add your NHS brand colours. This is the most important step.

Now, when you add a `<Button>` from Shadcn, it will automatically use your `primary` (NHS Blue) colour. When you use a destructive button, it will use your `destructive` (NHS Red) colour. All focus rings will be your `ringColor` (NHS Amber).