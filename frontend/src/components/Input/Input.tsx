import { InputHTMLAttributes, useState } from 'react';
import styles from './Input.module.scss';
import cn from 'classnames';

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  label?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onClear?: () => void;
}

export const Input = ({ label, className, value, onChange, onClear, ...props }: InputProps) => {
  const [isFocused, setIsFocused] = useState(false);
  // Показываем крестик только для текстовых полей и если есть значение
  const showClear =
    !props.disabled &&
    !props.readOnly &&
    value !== undefined &&
    value !== null &&
    value !== '' &&
    ((props.type !== 'date' && props.type !== 'time') ||
      (typeof value === 'string' && value.length > 0));

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onClear) {
      onClear();
    } else if (onChange) {
      const syntheticEvent = {
        target: { value: '' },
      } as React.ChangeEvent<HTMLInputElement>;
      onChange(syntheticEvent);
    }
  };

  return (
    <div className={styles.wrapper}>
      {label && <label className={styles.label}>{label}</label>}
      <div className={cn(styles.inputWrapper, { [styles.focused]: isFocused })}>
        <input
          className={cn(styles.input, className)}
          value={value}
          onChange={onChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          {...props}
        />
        {showClear && (
          <button type="button" onClick={handleClear} className={styles.clearButton} tabIndex={-1}>
            ×
          </button>
        )}
      </div>
    </div>
  );
};
