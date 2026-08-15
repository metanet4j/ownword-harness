import type {ReactElement} from 'react';

export interface TextFieldProps {
  label?: string;
  description?: string;
  errorMessage?: string;
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  type?: 'text' | 'email' | 'password' | 'search' | 'tel' | 'url';
  size?: 'S' | 'M' | 'L' | 'XL';
  isDisabled?: boolean;
  isReadOnly?: boolean;
  isRequired?: boolean;
  isInvalid?: boolean;
  isQuiet?: boolean;
  onChange?: (value: string) => void;
}

export declare function TextField(props: TextFieldProps): ReactElement;
