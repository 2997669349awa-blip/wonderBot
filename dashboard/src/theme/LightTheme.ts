import type { ThemeTypes } from '@/types/themeTypes/ThemeType';

const PurpleTheme: ThemeTypes = {
  name: 'PurpleTheme',
  dark: true,
  variables: {
    'border-color': '#1e88e5',
    'carousel-control-size': 10
  },
  colors: {
    primary: '#5ee0c8',
    secondary: '#3aa8ff',
    info: '#5ee0c8',
    success: '#4ade80',
    accent: '#a78bfa',
    warning: '#fbbf24',
    error: '#ff6b6b',
    lightprimary: '#101c1a',
    lightsecondary: '#101820',
    lightsuccess: '#10251a',
    lighterror: '#261313',
    lightwarning: '#251e0f',
    primaryText: '#f2f4f7',
    secondaryText: '#c7ccd4',
    darkprimary: '#3ec7ac',
    darksecondary: '#2b8ad6',
    borderLight: '#23232c',
    border: '#2a2a34',
    inputBorder: '#3a3a46',
    containerBg: '#0a0a0e',
    surface: '#121218',
    'on-surface-variant': '#d8dce4',
    facebook: '#4267b2',
    twitter: '#1da1f2',
    linkedin: '#0e76a8',
    gray100: '#9aa0aa',
    primary200: '#8ff0dc',
    secondary200: '#7cc4ff',
    background: '#08080b',
    overlay: '#000000cc',
    codeBg: '#101016',
    preBg: 'rgb(10, 10, 14)',
    code: '#e8eaed',
    chatMessageBubble: '#17171e',
    mcpCardBg: '#14141b',
  }
};

export { PurpleTheme };
