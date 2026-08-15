import type {ReactElement, ReactNode} from 'react';

export interface TabsProps {
  children?: ReactNode;
  selectedKey?: string;
  defaultSelectedKey?: string;
  isDisabled?: boolean;
  onSelectionChange?: (key: string) => void;
}

export declare function Tabs(props: TabsProps): ReactElement;
