import type {ReactElement} from 'react';

export interface PickerProps {
  label?: string;
  description?: string;
  errorMessage?: string;
  items?: Array<{key: string; label: string}>;
  selectedKey?: string;
  defaultSelectedKey?: string;
  placeholder?: string;
  size?: 'S' | 'M' | 'L' | 'XL';
  isDisabled?: boolean;
  isQuiet?: boolean;
  isRequired?: boolean;
  isInvalid?: boolean;
  onSelectionChange?: (key: string) => void;
}

export declare function Picker(props: PickerProps): ReactElement;
