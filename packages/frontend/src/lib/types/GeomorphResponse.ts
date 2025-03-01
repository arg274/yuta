import type { GeomorphData } from './GeomorphData';
import type { GraphData } from './GraphData';

export interface GeomorphResponse {
	data: GeomorphData[];
	graph_data: GraphData;
}
