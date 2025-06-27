// src/components/BrontoBoxLogo.js - FOR src/assets/logo.png
import React from 'react';
import logoImage from '../assets/icon.png'; // Import the image

const BrontoBoxLogo = ({ 
  size = 'medium', // 'favicon', 'small', 'medium', 'large', 'xl', 'xxl', or custom number
  className = '',
  alt = 'BrontoBox Logo',
  ...props 
}) => {
  
  // Size configurations (in pixels)
  const sizes = {
    favicon: 16,
    small: 32,
    medium: 48,
    large: 64,
    xl: 100,
    xxl: 128
  };
  
  // Get size - if it's a number, use it directly, otherwise use preset
  const logoSize = typeof size === 'number' ? size : (sizes[size] || sizes.medium);
  
  return (
    <img
      src={logoImage}  // Use imported image
      alt={alt}
      width={logoSize}
      height={logoSize}
      className={`inline-block ${className}`}
      style={{
        maxWidth: '100%',
        height: 'auto',
        objectFit: 'contain'
      }}
      {...props}
    />
  );
};

// Convenience components for common use cases
export const BrontoBoxFavicon = (props) => (
  <BrontoBoxLogo size="favicon" {...props} />
);

export const BrontoBoxSmall = (props) => (
  <BrontoBoxLogo size="small" {...props} />
);

export const BrontoBoxMedium = (props) => (
  <BrontoBoxLogo size="medium" {...props} />
);

export const BrontoBoxLarge = (props) => (
  <BrontoBoxLogo size="large" {...props} />
);

export const BrontoBoxXL = (props) => (
  <BrontoBoxLogo size="xl" {...props} />
);

// Custom size component
export const BrontoBoxCustom = ({ size, ...props }) => (
  <BrontoBoxLogo size={size} {...props} />
);

export default BrontoBoxLogo;