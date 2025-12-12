import { useState, useRef, useEffect } from 'react';
import styles from './Select.module.scss';
import cn from 'classnames';

interface SelectProps {
  label?: string;
  options: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
  disabled?: boolean;
}

export const Select = ({ label, options, value, onChange, className, disabled }: SelectProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const selectRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find(opt => opt.value === value) || options[0];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleSelect = (optionValue: string) => {
    onChange(optionValue);
    setIsOpen(false);
  };

  return (
    <div className={cn(styles.wrapper, className)} ref={selectRef}>
      {label && <label className={styles.label}>{label}</label>}
      <div
        className={cn(styles.select, { [styles.open]: isOpen, [styles.disabled]: disabled })}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        <span className={styles.selectedValue}>{selectedOption?.label || ''}</span>
        <span className={styles.arrow}>▼</span>
      </div>
      {isOpen && (
        <div className={styles.dropdown}>
          {options.map(option => (
            <div
              key={option.value}
              className={cn(styles.option, {
                [styles.selected]: option.value === value,
              })}
              onClick={() => handleSelect(option.value)}
            >
              {option.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
