# NHS Network Analysis - Geographic Visualization Handover

## 🎯 **Hack MVP Goal**
Transform existing network analysis into a map-based visualization showing NHS patient-site communities across **North West London** with risk-based color coding.

---

## 📋 **What You're Getting**

### **Working System** ✅
- FastAPI web app with Leiden community detection
- 68 patient-site communities identified with risk levels
- JSON export with ~18K nodes and geographic data
- Risk classification: High (red), Medium (orange), Low (green)

### **Geographic Data Available**
```json
// Patient nodes have postcodes
{
  "id": "P_12345",
  "type": "patient", 
  "postcode": "NW1 2AB",
  "risk_level": "High",
  "community": 5
}

// Site nodes have locations  
{
  "id": "S_ABC123",
  "type": "site",
  "location": "HARROW",
  "org_code": "ABC123" 
}
```

---

## 🗺️ **MVP Map Requirements (30min implementation)**

### **1. Simple Leaflet Map**
```html
<!-- Add to visualization.html -->
<div id="map-container" style="height: 600px; width: 100%;"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
```

### **2. NW London Bounds**
```javascript
// Center on NW London
const map = L.map('map-container').setView([51.5574, -0.2794], 11);
const bounds = [[51.4500, -0.5500], [51.6500, -0.0500]]; // NW London rough bounds
map.fitBounds(bounds);
```

### **3. Quick Postcode→Coordinates**
Two hack-friendly options:

**Option A: Hardcode Major NW London Postcodes (5min)**
```javascript
const nwLondonCoords = {
  "NW1": [51.5273, -0.1278], "NW2": [51.5605, -0.2239],
  "NW3": [51.5479, -0.1726], "NW4": [51.6094, -0.2297],
  "NW5": [51.5519, -0.1428], "NW6": [51.5440, -0.1933],
  "NW7": [51.6049, -0.2452], "NW8": [51.5342, -0.1684],
  "NW9": [51.6044, -0.2647], "NW10": [51.5305, -0.2416],
  "NW11": [51.5767, -0.2169], "W1": [51.5154, -0.1426],
  "W2": [51.5154, -0.1807], "W3": [51.5088, -0.2478],
  "HA0": [51.5723, -0.3154], "HA1": [51.5723, -0.3365],
  // Add more as needed
};

function getCoords(postcode) {
  const area = postcode.substring(0, postcode.indexOf(' ')); 
  return nwLondonCoords[area] || [51.5574, -0.2794]; // Default to center
}
```

**Option B: Free Postcode API (10min)**
```javascript
async function geocodePostcode(postcode) {
  try {
    const response = await fetch(`https://api.postcodes.io/postcodes/${postcode}`);
    const data = await response.json();
    return [data.result.latitude, data.result.longitude];
  } catch {
    return [51.5574, -0.2794]; // Fallback to NW London center
  }
}
```

### **4. Plot Communities on Map**
```javascript
// Color by risk level
const riskColors = {
  'High': '#d32f2f',
  'Medium': '#ff9800', 
  'Low': '#4caf50'
};

// Add markers for each community
networkData.nodes.forEach(async (node) => {
  if (node.type === 'patient') {
    const coords = await getCoords(node.postcode);
    
    L.circleMarker(coords, {
      radius: 8,
      fillColor: riskColors[node.risk_level],
      color: '#333',
      weight: 1,
      opacity: 1,
      fillOpacity: 0.7
    })
    .bindPopup(`
      <b>Community ${node.community}</b><br>
      Risk: ${node.risk_level}<br>
      DNA Rate: ${(node.dna_rate * 100).toFixed(1)}%
    `)
    .addTo(map);
  }
});
```

---

## 🚀 **Quick Implementation Steps**

### **Step 1: Add Map Container (1min)**
Add map div to `templates/visualization.html` next to the network viz

### **Step 2: Add Leaflet (1min)** 
Include Leaflet CSS/JS from CDN

### **Step 3: Initialize Map (2min)**
Create map focused on NW London bounds

### **Step 4: Plot Points (10min)**
- Use hardcoded postcode coordinates OR
- Call postcodes.io API for each unique postcode

### **Step 5: Style by Risk (5min)**
Color circles red/orange/green based on `risk_level`

### **Step 6: Add Interactivity (10min)**
- Popups with community info
- Click to highlight network connections
- Toggle between map and network view

---

## 📁 **Files to Modify**

### **templates/visualization.html**
- Add map container div
- Include Leaflet CSS/JS  
- Add postcode geocoding function
- Plot community markers with risk colors

### **webapp.py** (Optional)
- Add `/map` endpoint if you want separate map page
- Pre-process postcodes to coordinates server-side

---

## 🎨 **Visual Design**

### **Risk-Based Styling**
- **High Risk Communities**: Large red circles (radius 12px)
- **Medium Risk**: Orange circles (radius 8px) 
- **Low Risk**: Green circles (radius 6px)
- **Healthcare Sites**: Blue squares or hospital icons

### **Clustering** 
For dense areas, use Leaflet.markercluster:
```html
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
```

---

## 🔍 **Geographic Insights to Highlight**

1. **Geographic DNA Hotspots** - clusters of high-risk communities
2. **Site Accessibility** - distance patterns between patients and sites  
3. **Transport Links** - communities near tube stations vs. isolated areas
4. **Socioeconomic Correlation** - overlay with deprivation indices
5. **Service Gaps** - areas with high patient concentration but few sites

---

## 📊 **Data Access**

### **Get Map Data**
```javascript
// From existing webapp
fetch('/graph-data')
  .then(response => response.json())
  .then(data => {
    // data.nodes contains all patient/site info
    // data.communities contains risk analysis
    plotOnMap(data);
  });
```

### **Available Fields**
- `postcode`: Patient postcodes (e.g., "NW1 2AB")  
- `location`: Site locations (e.g., "HARROW")
- `risk_level`: "High", "Medium", "Low"
- `community`: Community ID (0-67)
- `dna_rate`: DNA rate as decimal (0.0-1.0)

---

## ⚡ **Hack Shortcuts**

### **Don't Over-Engineer**
- Hardcode NW London postcode coordinates
- Use simple circle markers, not fancy icons
- Skip clustering unless you have >1000 points visible
- One color per risk level, keep it simple

### **Copy-Paste Ready**
```javascript
// Complete MVP in one block
const map = L.map('map-container').setView([51.5574, -0.2794], 11);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

const riskColors = {'High': '#d32f2f', 'Medium': '#ff9800', 'Low': '#4caf50'};

// Hardcoded NW London coordinates  
const coords = {"NW1": [51.5273, -0.1278], "NW2": [51.5605, -0.2239], "NW3": [51.5479, -0.1726]};

networkData.nodes.forEach(node => {
  if (node.type === 'patient') {
    const area = node.postcode?.substring(0, node.postcode.indexOf(' ')) || 'NW1';
    const latLng = coords[area] || [51.5574, -0.2794];
    
    L.circleMarker(latLng, {
      radius: 8, fillColor: riskColors[node.risk_level], 
      color: '#333', weight: 1, fillOpacity: 0.7
    }).bindPopup(`Community ${node.community}: ${node.risk_level} Risk`).addTo(map);
  }
});
```

---

## 🎯 **Expected Result**

A map of North West London showing:
- **Red clusters** = High-risk patient communities  
- **Orange/Green dots** = Medium/Low risk communities
- **Click interactions** = Show community details
- **Geographic patterns** = Visual DNA rate distribution across NW London

**Total implementation time: ~30 minutes for MVP** 🚀

---

## 🔧 **Integration Points**

The existing webapp provides:
- `/graph-data` endpoint with all community data
- Risk classification already calculated  
- Community IDs for cross-referencing
- Postcode data ready to geocode

Just add the map container and plotting logic to the existing visualization page!

---

**Ready for geographic specialist handover** ✅