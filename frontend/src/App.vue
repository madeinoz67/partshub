<template>
  <div id="q-app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// PartsHub main app component
</script>

<style lang="scss">
#q-app {
  height: 100vh;
}

// Global styles for the application
body {
  font-family: 'Roboto', sans-serif;
}

// Utility classes
.full-width {
  width: 100%;
}

.text-weight-medium {
  font-weight: 500;
}

// Status color overrides
.text-positive {
  color: #4caf50 !important;
}

.text-negative {
  color: #f44336 !important;
}

.text-warning {
  color: #ff9800 !important;
}

// Card enhancements
.q-card {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);

  &:hover {
    box-shadow: 0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23);
  }
}

// Global button styles
.add-button {
  // Standard sizing to match Quasar default
  min-height: 32px;
  padding: 8px 16px;

  // Responsive text behavior
  .add-text-full {
    display: inline;
  }

  .add-text-short {
    display: none;
  }

  // Mobile responsive
  @media (max-width: 599px) {
    .add-text-full {
      display: none;
    }

    .add-text-short {
      display: inline;
    }
  }
}

// Primary add button variant
.add-button-primary {
  @extend .add-button;
  background-color: #1976d2;
  color: white;

  &:hover {
    background-color: #1565c0;
  }
}

// Standardized container for add buttons next to search fields
// These classes provide consistent sizing for buttons across Components, Projects, and Storage Locations pages
// The col-md-* and col-xs-* classes ensure proper responsive behavior and button height
.add-button-container-short {
  // For buttons with short labels like "Add", "New"
  // Note: This is a placeholder for future use if needed
}

.add-button-container-long {
  // For buttons with longer labels like "Add Component", "Create Bulk Locations", "New Project"
  // This ensures consistent button height and layout across all pages
}
</style>