# rational_onion/api/dag_visualization.py

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from rational_onion.services.neo4j_service import driver

router = APIRouter()

@router.get("/visualize-argument-dag")
async def visualize_argument_dag():
    """
    Returns the argument DAG structure for front-end visualization (D3.js, Cytoscape.js).
    """
    async with driver.session() as session:
        result = await session.run("""
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN collect(DISTINCT {id: ID(n), label: labels(n)[0], text: n.text}) AS nodes,
                   collect(DISTINCT {source: ID(n), target: ID(m), type: type(r)}) AS edges
        """)
        record = await result.single()
        graph = {
            "nodes": record["nodes"] if record else [],
            "edges": record["edges"] if record else []
        }
        return JSONResponse(content=graph)