/**
 * International Size Conversion Utility
 * Converts between US, UK, EU, and other international sizing systems
 */

export const SIZE_CONVERSION_TABLE = {
  'XS': {
    us: ['0', '2'],
    uk: ['4', '6'],
    au: ['4', '6'],
    nz: ['4', '6'],
    italy: ['36', '38'],
    france: ['32', '34'],
    germany: ['30', '32'],
    japan: ['5', '7'],
    russia: ['38', '40']
  },
  'S': {
    us: ['2', '4'],
    uk: ['6', '8'],
    au: ['6', '8'],
    nz: ['6', '8'],
    italy: ['38', '40'],
    france: ['34', '36'],
    germany: ['32', '34'],
    japan: ['7', '9'],
    russia: ['40', '42']
  },
  'M': {
    us: ['6', '8'],
    uk: ['10', '12'],
    au: ['10', '12'],
    nz: ['10', '12'],
    italy: ['42', '44'],
    france: ['38', '40'],
    germany: ['36', '38'],
    japan: ['11', '13'],
    russia: ['44', '46']
  },
  'L': {
    us: ['10', '12'],
    uk: ['14', '16'],
    au: ['14', '16'],
    nz: ['14', '16'],
    italy: ['46', '48'],
    france: ['42', '44'],
    germany: ['40', '42'],
    japan: ['15', '17'],
    russia: ['48', '50']
  },
  'XL': {
    us: ['14', '16'],
    uk: ['18', '20'],
    au: ['18', '20'],
    nz: ['18', '20'],
    italy: ['50', '52'],
    france: ['46', '48'],
    germany: ['44', '46'],
    japan: ['19', '21'],
    russia: ['52', '54']
  },
  '1X': {
    us: ['14', '16'],
    uk: ['18', '20'],
    au: ['18', '20'],
    nz: ['18', '20'],
    italy: ['50', '52'],
    france: ['46', '48'],
    germany: ['44', '46'],
    japan: ['19', '21'],
    russia: ['52', '54']
  },
  '2X': {
    us: ['18', '20'],
    uk: ['22', '24'],
    au: ['22', '24'],
    nz: ['22', '24'],
    italy: ['54', '56'],
    france: ['50', '52'],
    germany: ['48', '50'],
    japan: ['23', '25'],
    russia: ['56', '58']
  },
  '3X': {
    us: ['20', '22'],
    uk: ['24', '26'],
    au: ['24', '26'],
    nz: ['24', '26'],
    italy: ['56', '58'],
    france: ['52', '54'],
    germany: ['50', '52'],
    japan: ['25', '27'],
    russia: ['58', '60']
  },
  '4X': {
    us: ['24'],
    uk: ['28'],
    au: ['28'],
    nz: ['28'],
    italy: ['60'],
    france: ['56'],
    germany: ['54'],
    japan: ['29'],
    russia: ['62']
  }
};

export const REGION_LABELS = {
  us: 'US',
  uk: 'UK',
  au: 'AU',
  nz: 'NZ',
  italy: 'Italy',
  france: 'France',
  germany: 'Germany',
  japan: 'Japan',
  russia: 'Russia',
  eu: 'EU'
};

/**
 * Get size conversions for a given size
 * @param {string} size - Base size (XS, S, M, L, XL, 1X, 2X, 3X, 4X)
 * @returns {object} Size conversions for all regions
 */
export const getSizeConversions = (size) => {
  const normalizedSize = size.toUpperCase();
  return SIZE_CONVERSION_TABLE[normalizedSize] || null;
};

/**
 * Format size with region conversions for display
 * @param {string} size - Base size
 * @param {array} regions - Array of regions to show (default: ['us', 'uk', 'eu'])
 * @returns {string} Formatted size string
 */
export const formatSizeWithConversions = (size, regions = ['us', 'uk', 'italy']) => {
  const conversions = getSizeConversions(size);

  if (!conversions) {
    return size;
  }

  const parts = [size];

  regions.forEach(region => {
    if (conversions[region]) {
      const regionSizes = conversions[region];
      const label = REGION_LABELS[region];

      if (regionSizes.length === 1) {
        parts.push(`${label} ${regionSizes[0]}`);
      } else {
        parts.push(`${label} ${regionSizes[0]}-${regionSizes[regionSizes.length - 1]}`);
      }
    }
  });

  return parts.join(' | ');
};

/**
 * Get all size equivalents as a formatted object
 * @param {string} size - Base size
 * @returns {object} Object with region labels and size arrays
 */
export const getAllSizeEquivalents = (size) => {
  const conversions = getSizeConversions(size);

  if (!conversions) {
    return {};
  }

  const result = { base: size };

  Object.keys(conversions).forEach(region => {
    result[region] = {
      label: REGION_LABELS[region],
      sizes: conversions[region]
    };
  });

  return result;
};

/**
 * Create a size guide tooltip content
 * @param {string} size - Base size
 * @returns {string} HTML string for tooltip
 */
export const createSizeGuideTooltip = (size) => {
  const conversions = getSizeConversions(size);

  if (!conversions) {
    return `Size: ${size}`;
  }

  const lines = [`<strong>Size: ${size}</strong>`];

  const regionOrder = ['us', 'uk', 'au', 'italy', 'france', 'germany', 'japan'];

  regionOrder.forEach(region => {
    if (conversions[region]) {
      const regionSizes = conversions[region].join(', ');
      lines.push(`${REGION_LABELS[region]}: ${regionSizes}`);
    }
  });

  return lines.join('<br>');
};

/**
 * Get size guide table data for all sizes
 * @returns {array} Array of size objects with all conversions
 */
export const getSizeGuideTable = () => {
  return Object.keys(SIZE_CONVERSION_TABLE).map(size => {
    return {
      size,
      ...SIZE_CONVERSION_TABLE[size]
    };
  });
};

/**
 * Check if a size exists in the conversion table
 * @param {string} size - Size to check
 * @returns {boolean} True if size exists
 */
export const isValidSize = (size) => {
  return SIZE_CONVERSION_TABLE.hasOwnProperty(size.toUpperCase());
};

/**
 * Get user's preferred region from browser settings
 * @returns {string} Region code (us, uk, etc.)
 */
export const getUserRegion = () => {
  const locale = navigator.language || navigator.userLanguage || 'en-US';

  if (locale.startsWith('en-GB')) return 'uk';
  if (locale.startsWith('en-AU')) return 'au';
  if (locale.startsWith('en-NZ')) return 'nz';
  if (locale.startsWith('it')) return 'italy';
  if (locale.startsWith('fr')) return 'france';
  if (locale.startsWith('de')) return 'germany';
  if (locale.startsWith('ja')) return 'japan';
  if (locale.startsWith('ru')) return 'russia';

  return 'us'; // Default to US
};

/**
 * Format size for display based on user's region
 * @param {string} size - Base size
 * @param {string} userRegion - User's region (optional, auto-detected if not provided)
 * @returns {string} Formatted size string
 */
export const formatSizeForRegion = (size, userRegion = null) => {
  const region = userRegion || getUserRegion();
  const conversions = getSizeConversions(size);

  if (!conversions || region === 'us') {
    return size; // Return base size if no conversion or US region
  }

  if (conversions[region]) {
    const regionSizes = conversions[region];
    return `${size} (${REGION_LABELS[region]} ${regionSizes.join('/')})`;
  }

  return size;
};

export default {
  getSizeConversions,
  formatSizeWithConversions,
  getAllSizeEquivalents,
  createSizeGuideTooltip,
  getSizeGuideTable,
  isValidSize,
  getUserRegion,
  formatSizeForRegion,
  SIZE_CONVERSION_TABLE,
  REGION_LABELS
};
