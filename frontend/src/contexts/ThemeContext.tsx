import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  effectiveTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    // Load saved theme from localStorage; default to light
    const savedTheme = localStorage.getItem('chatmrpt_theme') as Theme | null;
    return savedTheme === 'dark' || savedTheme === 'light' ? savedTheme : 'light';
  });
  
  const [effectiveTheme, setEffectiveTheme] = useState<'light' | 'dark'>('light');
  
  // Determine effective theme based on user preference or system
  useEffect(() => {
    const applyTheme = () => {
      const appliedTheme: 'light' | 'dark' = theme === 'dark' ? 'dark' : 'light';
      
      setEffectiveTheme(appliedTheme);
      
      // Apply theme to document root
      if (appliedTheme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    };
    
    applyTheme();
    
    // No system mode handling
  }, [theme]);
  
  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem('chatmrpt_theme', newTheme);
  };
  
  return (
    <ThemeContext.Provider value={{ theme, effectiveTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
