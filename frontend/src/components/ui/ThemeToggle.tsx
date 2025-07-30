import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import { motion, AnimatePresence } from 'framer-motion';

interface ThemeToggleProps {
  variant?: 'button' | 'dropdown';
  className?: string;
}

export function ThemeToggle({ variant = 'button', className = '' }: ThemeToggleProps) {
  const { theme, setTheme } = useTheme();

  if (variant === 'dropdown') {
    return (
      <div className={`relative ${className}`}>
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
          className="
            bg-[var(--ctan-card)] border border-[var(--ctan-border)] rounded-md px-3 py-2 text-sm
            text-[var(--ctan-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--ctan-gold)]/50
            focus:border-[var(--ctan-gold)]/50 transition-all duration-200
          "
        >
          <option value="light">Light</option>
          <option value="dark">Dark</option>
          <option value="system">System</option>
        </select>
      </div>
    );
  }

  const themes = [
    { value: 'light', icon: Sun, label: 'Light' },
    { value: 'dark', icon: Moon, label: 'Dark' },
    { value: 'system', icon: Monitor, label: 'System' },
  ] as const;

  return (
    <div className={`flex items-center bg-[var(--ctan-card)] border border-[var(--ctan-border)] rounded-lg p-1 ${className}`}>
      {themes.map(({ value, icon: Icon, label }) => (
        <motion.button
          key={value}
          onClick={() => setTheme(value)}
          className={`
            relative flex items-center justify-center w-8 h-8 rounded-md transition-all duration-200
            ${theme === value 
              ? 'text-[var(--ctan-bg)]' 
              : 'text-[var(--ctan-text-secondary)] hover:text-[var(--ctan-text-primary)] hover:bg-[var(--ctan-hover)]'
            }
          `}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          title={`${label} theme`}
        >
          <AnimatePresence>
            {theme === value && (
              <motion.div
                className="absolute inset-0 bg-[var(--ctan-gold)] rounded-md"
                layoutId="theme-indicator"
                initial={false}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
              />
            )}
          </AnimatePresence>
          <Icon 
            size={16} 
            className="relative z-10" 
          />
        </motion.button>
      ))}
    </div>
  );
}

// Simplified toggle button for minimal UI
export function SimpleThemeToggle({ className = '' }: { className?: string }) {
  const { actualTheme, setTheme } = useTheme();

  const toggleTheme = () => {
    setTheme(actualTheme === 'dark' ? 'light' : 'dark');
  };

  return (
    <motion.button
      onClick={toggleTheme}
      className={`
        flex items-center justify-center w-10 h-10 rounded-full
        bg-[var(--ctan-card)] border border-[var(--ctan-border)]
        text-[var(--ctan-text-primary)] hover:text-[var(--ctan-gold)]
        hover:border-[var(--ctan-gold)]/30 hover:bg-[var(--ctan-hover)]
        transition-all duration-200
        ${className}
      `}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      title={`Switch to ${actualTheme === 'dark' ? 'light' : 'dark'} theme`}
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={actualTheme}
          initial={{ rotate: -180, opacity: 0 }}
          animate={{ rotate: 0, opacity: 1 }}
          exit={{ rotate: 180, opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {actualTheme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </motion.div>
      </AnimatePresence>
    </motion.button>
  );
}