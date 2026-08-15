import type {ReactElement} from 'react';

export interface SearchFieldProps {
  label?: string;
  description?: string;
  errorMessage?: string;
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  isDisabled?: boolean;
  isQuiet?: boolean;
  onSubmit?: (value: string) => void;
}

export declare function SearchField(props: SearchFieldProps): ReactElement;
