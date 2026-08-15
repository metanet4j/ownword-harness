import type {ReactElement} from 'react';

export interface ComboBoxProps {
  label?: string;
  description?: string;
  errorMessage?: string;
  inputValue?: string;
  defaultInputValue?: string;
  items?: Array<{key: string; label: string}>;
  size?: 'S' | 'M' | 'L' | 'XL';
  isDisabled?: boolean;
  isQuiet?: boolean;
  isRequired?: boolean;
  isInvalid?: boolean;
  onInputChange?: (value: string) => void;
}

export declare function ComboBox(props: ComboBoxProps): ReactElement;
