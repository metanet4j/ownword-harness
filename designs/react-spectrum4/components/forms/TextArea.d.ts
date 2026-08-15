import type {ReactElement} from 'react';

export interface TextAreaProps {
  label?: string;
  description?: string;
  errorMessage?: string;
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  size?: 'S' | 'M' | 'L' | 'XL';
  isDisabled?: boolean;
  isReadOnly?: boolean;
  isRequired?: boolean;
  isInvalid?: boolean;
  onChange?: (value: string) => void;
}

export declare function TextArea(props: TextAreaProps): ReactElement;
