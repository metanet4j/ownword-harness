import type {ReactElement} from 'react';

export interface NumberFieldProps {
  label?: string;
  description?: string;
  errorMessage?: string;
  value?: number;
  defaultValue?: number;
  minValue?: number;
  maxValue?: number;
  step?: number;
  size?: 'S' | 'M' | 'L' | 'XL';
  isDisabled?: boolean;
  isReadOnly?: boolean;
  isRequired?: boolean;
  isInvalid?: boolean;
  onChange?: (value: number) => void;
}

export declare function NumberField(props: NumberFieldProps): ReactElement;
