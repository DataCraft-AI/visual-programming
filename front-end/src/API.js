import { downloadFile } from './utils';


/**
 * Sends request to server via fetch API and handles error cases
 * @param {string} endpoint - server endpoint
 * @param {Object} options - options parameter for `fetch` call
 * @returns {Promise<Object>} - server response or error
 */
function fetchWrapper(endpoint, options = {}) {
       return new Promise((resolve, reject) => {
        fetch(endpoint, options)
            .then(async resp => {
                const data = await resp.json();
                console.log(data);
                if (resp.ok) return resolve(data);
                else return reject(data);
            })
            .catch(err => {
                return reject(err);
            });
    });
}


/**
 * Add node to server-side workflow
 * @param {CustomNodeModel} node - JS node to add
 * @returns {Promise<Object>} - server response
 */
export async function addNode(node) {
    const payload = {...node.options, options: node.config};
    const options = {
        method: "POST",
        body: JSON.stringify(payload)
    };
    return fetchWrapper("/node/", options);
}


/**
 * Delete node from server-side workflow
 * @param {CustomNodeModel} node - JS node to remove
 * @returns {Promise<Object>} - server response
 */
export async function deleteNode(node) {
    const id = node.options.id;
    const options = {
        method: "DELETE"
    };
    return fetchWrapper(`/node/${id}`, options);
}


/**
 * Update configuration of node in server-side workflow
 * @param {CustomNodeModel} node - JS node to remove
 * @param {Object} config - configuration from options form
 * @returns {Promise<Object>} - server response (serialized node)
 */
export async function updateNode(node, config) {
    node.config = config;
    const payload = {...node.options, options: node.config};
    const options = {
        method: "POST",
        body: JSON.stringify(payload)
    };
    return fetchWrapper(`/node/${node.options.id}`, options)
}


/**
 * Save front-end workflow and download server response as JSON file
 * @param {Object} diagramData - serialized react-diagrams model
 */
export async function save(diagramData) {
    const payload = JSON.stringify(diagramData);
    const options = {
        method: "POST",
        body: payload
    };
    fetchWrapper("/workflow/save", options)
        .then(json => {
            downloadFile(JSON.stringify(json), "application/json",
                json.filename || "diagram.json")
        }).catch(err => console.log(err));
}


/**
 * Get available nodes for node menu
 * @returns {Promise<Object>} - server response (node menu items)
 */
export async function getNodes() {
    return fetchWrapper("/nodes");
}


/**
 * Start a new workflow on the server
 * @returns {Promise<Object>} - server response
 */
export async function initWorkflow() {
    return fetchWrapper("/workflow/new");
}


/**
 * Uploads JSON workflow file to server
 * @param {FormData} formData - form with key `file` and value of type `File`
 * @returns {Promise<Object>} - server response (full serialized workflow)
 */
export async function uploadWorkflow(formData) {
    const options = {
        method: "POST",
        body: formData
    };
    return fetchWrapper("/workflow/open", options);
}


async function handleEdge(link, method) {
    const sourceId = link.getSourcePort().getNode().options.id;
    const targetId = link.getTargetPort().getNode().options.id;
    return fetchWrapper(
        `/node/edge/${sourceId}/${targetId}`,
        {method: method});
}


/**
 * Add edge to server-side workflow
 * @param {VPLinkModel} link - JS edge to create
 * @returns {Promise<Object>} - server response
 */
export async function addEdge(link) {
    return handleEdge(link, "POST");
}


/**
 * Delete edge from server-side workflow
 * @param {VPLinkModel} link - JS edge to delete
 * @returns {Promise<Object>} - server response
 */
export async function deleteEdge(link) {
    return handleEdge(link, "DELETE");
}


/**
 * Upload a data file to be stored on the server
 * @param {FormData} formData - FormData with file and nodeId
 * @returns {Promise<Object>} - server response
 */
export async function uploadDataFile(formData) {
    const options = {
        method: "POST",
        body: formData
    };
    return fetchWrapper("/workflow/upload", options);
}


/**
 * Download file by name from server
 * @param {CustomNodeModel} node - node containing file to download
 * @returns {Promise<void>}
 */
export async function downloadDataFile(node) {
    // TODO: make this not a giant security problem
    let contentType;

    const payload = {...node.options, options: node.config};

    // can't use fetchWrapper because it assumes JSON response
    fetch(`/workflow/download`, {
        method: "POST",
        body: JSON.stringify(payload)
    })
        .then(async resp => {
            if (!resp.ok) return Promise.reject(await resp.json());
            contentType = resp.headers.get("content-type");
            if (contentType.startsWith("text")) {
                resp.text().then(data => {
                    downloadFile(data, contentType, node.config["path_or_buf"]);
                })
            }
        }).catch(err => console.log(err));
}


/**
 * Get execution order of nodes in graph
 * @returns {Promise<Object>} - server response (array of node IDs)
 */
export async function executionOrder() {
    return fetchWrapper("/workflow/execute");
}

/**
 * Execute given node on server
 * @param {CustomNodeModel }node - node to execute
 * @returns {Promise<Object>} - server response
 */
export async function execute(node) {
    const id = node.options.id;
    return fetchWrapper(`/node/${id}/execute`);
}