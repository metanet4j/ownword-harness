import type {ReactElement, ReactNode} from 'react';

export interface ProviderProps {
  children?: ReactNode;
  colorScheme?: 'light' | 'dark' | 'darkest' | 'lightest';
  scale?: 'medium' | 'large';
  background?: 'base' | 'layer-1' | 'layer-2';
  locale?: string;
}

export declare function Provider(props: ProviderProps): ReactElement;
