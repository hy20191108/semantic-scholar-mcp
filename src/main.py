"""Main application entry point with enterprise configuration.

This module demonstrates how to use all the enterprise patterns together
to create a production-ready Semantic Scholar MCP server.
"""

import asyncio
import logging
import signal
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server

from core.abstractions import ILogger, IMetricsCollector
from core.cache import CacheManager
from core.config import Environment, get_config
from core.container import configure_services, set_current_scope
from core.metrics import HealthCheck
from semantic_scholar_mcp.api_client_enhanced import EnhancedSemanticScholarClient


class SemanticScholarMCPServer:
    """Main MCP server with enterprise features.
    
    Examples:
        >>> # Start server with custom configuration
        >>> server = SemanticScholarMCPServer(environment="production")
        >>> await server.run()
        
        >>> # Health check endpoint
        >>> health = await server.health_check()
        >>> print(health["status"])
        'healthy'
    """

    def __init__(self, environment: str | None = None) -> None:
        """Initialize MCP server."""
        # Load configuration
        self.config = get_config()
        if environment:
            self.config.environment = Environment.from_string(environment)

        # Validate configuration for environment
        self.config.validate_for_environment()

        # Configure services
        self.service_provider = configure_services(self.config)

        # Get core services
        self.logger = self.service_provider.get_required_service(ILogger)
        self.metrics = self.service_provider.get_required_service(IMetricsCollector)

        # Initialize cache
        self.cache = CacheManager(
            self.config.cache,
            self.logger,
            self.metrics
        )

        # Initialize API client
        self.api_client: EnhancedSemanticScholarClient | None = None

        # Initialize health check
        self.health_check_service = HealthCheck(self.metrics)

        # Initialize MCP server
        self.mcp_server = Server("semantic-scholar-mcp")

        # Set up signal handlers
        self._setup_signal_handlers()

        # Log startup
        self.logger.info(
            "Semantic Scholar MCP Server initialized",
            environment=self.config.environment.value,
            version=self.config.app_version
        )

    async def initialize(self) -> None:
        """Initialize all services."""
        self.logger.info("Initializing services")

        # Create service scope
        scope = self.service_provider.create_scope()
        set_current_scope(scope)

        try:
            # Initialize API client
            self.api_client = EnhancedSemanticScholarClient(
                config=self.config.api,
                logger=self.logger,
                metrics=self.metrics,
                cache=self.cache
            )
            await self.api_client.initialize()

            # Register health checks
            self.health_check_service.register_check(
                "api_client",
                lambda: asyncio.run(self.api_client.health_check())
            )

            self.health_check_service.register_check(
                "cache",
                lambda: asyncio.run(self._check_cache_health())
            )

            # Register MCP tools
            self._register_mcp_tools()

            self.logger.info("All services initialized successfully")

        except Exception as e:
            self.logger.error("Failed to initialize services", exception=e)
            raise

    def _register_mcp_tools(self) -> None:
        """Register MCP tools."""

        @self.mcp_server.tool()
        async def search_papers(query: str, limit: int = 10) -> dict:
            """Search for papers on Semantic Scholar.
            
            Args:
                query: Search query string
                limit: Maximum number of results (default: 10)
                
            Returns:
                Search results with paper information
            """
            async with self.logger.log_context(tool="search_papers", query=query):
                try:
                    results = await self.api_client.search_papers(
                        query=query,
                        limit=limit
                    )

                    return {
                        "total": results.total,
                        "papers": [
                            {
                                "id": paper.paper_id,
                                "title": paper.title,
                                "year": paper.year,
                                "authors": [a.name for a in paper.authors],
                                "citation_count": paper.citation_count,
                                "abstract": paper.abstract[:200] + "..." if paper.abstract else None
                            }
                            for paper in results.data
                        ]
                    }
                except Exception as e:
                    self.logger.error("Search failed", exception=e)
                    return {"error": str(e)}

        @self.mcp_server.tool()
        async def get_paper(paper_id: str, include_references: bool = False) -> dict:
            """Get detailed information about a paper.
            
            Args:
                paper_id: Paper ID (Semantic Scholar ID, DOI, or ArXiv ID)
                include_references: Include paper references
                
            Returns:
                Detailed paper information
            """
            async with self.logger.log_context(tool="get_paper", paper_id=paper_id):
                try:
                    paper = await self.api_client.get_paper(
                        paper_id=paper_id,
                        include_references=include_references
                    )

                    result = {
                        "id": paper.paper_id,
                        "title": paper.title,
                        "abstract": paper.abstract,
                        "year": paper.year,
                        "venue": paper.venue,
                        "authors": [
                            {"name": a.name, "id": a.author_id}
                            for a in paper.authors
                        ],
                        "citation_count": paper.citation_count,
                        "influential_citation_count": paper.influential_citation_count,
                        "reference_count": paper.reference_count,
                        "fields_of_study": paper.fields_of_study,
                        "url": paper.url,
                        "doi": paper.doi,
                        "arxiv_id": paper.arxiv_id
                    }

                    if include_references and hasattr(paper, "references"):
                        result["references"] = [
                            {
                                "id": ref.paper_id,
                                "title": ref.title,
                                "year": ref.year
                            }
                            for ref in paper.references[:10]
                        ]

                    return result

                except Exception as e:
                    self.logger.error("Get paper failed", exception=e)
                    return {"error": str(e)}

        @self.mcp_server.tool()
        async def get_author(author_id: str, papers_limit: int = 10) -> dict:
            """Get detailed information about an author.
            
            Args:
                author_id: Author ID
                papers_limit: Maximum number of papers to include
                
            Returns:
                Detailed author information
            """
            async with self.logger.log_context(tool="get_author", author_id=author_id):
                try:
                    author = await self.api_client.get_author(
                        author_id=author_id,
                        papers_limit=papers_limit
                    )

                    return {
                        "id": author.author_id,
                        "name": author.name,
                        "aliases": author.aliases,
                        "affiliations": author.affiliations,
                        "homepage": author.homepage,
                        "paper_count": author.paper_count,
                        "citation_count": author.citation_count,
                        "h_index": author.h_index,
                        "papers": [
                            {
                                "id": p.paper_id,
                                "title": p.title,
                                "year": p.year,
                                "citation_count": p.citation_count
                            }
                            for p in author.papers
                        ]
                    }

                except Exception as e:
                    self.logger.error("Get author failed", exception=e)
                    return {"error": str(e)}

        @self.mcp_server.tool()
        async def get_recommendations(paper_id: str, limit: int = 10) -> dict:
            """Get paper recommendations based on a paper.
            
            Args:
                paper_id: Paper ID to base recommendations on
                limit: Maximum number of recommendations
                
            Returns:
                List of recommended papers
            """
            async with self.logger.log_context(tool="get_recommendations", paper_id=paper_id):
                try:
                    recommendations = await self.api_client.get_recommendations(
                        paper_id=paper_id,
                        limit=limit
                    )

                    return {
                        "recommendations": [
                            {
                                "id": paper.paper_id,
                                "title": paper.title,
                                "year": paper.year,
                                "authors": [a.name for a in paper.authors],
                                "citation_count": paper.citation_count,
                                "abstract": paper.abstract[:200] + "..." if paper.abstract else None
                            }
                            for paper in recommendations
                        ]
                    }

                except Exception as e:
                    self.logger.error("Get recommendations failed", exception=e)
                    return {"error": str(e)}

        self.logger.info("MCP tools registered", count=4)

    async def health_check(self) -> dict:
        """Perform comprehensive health check."""
        return await self.health_check_service.check_health()

    async def _check_cache_health(self) -> dict:
        """Check cache health."""
        try:
            # Try basic cache operations
            test_key = "health_check_test"
            test_value = {"test": True, "timestamp": datetime.utcnow().isoformat()}

            await self.cache.set(test_key, test_value, ttl=60)
            retrieved = await self.cache.get(test_key)
            await self.cache.delete(test_key)

            # Get cache stats
            stats = await self.cache.get_stats()

            return {
                "status": "healthy" if retrieved == test_value else "unhealthy",
                "stats": stats
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    async def shutdown(self) -> None:
        """Gracefully shutdown all services."""
        self.logger.info("Shutting down services")

        try:
            # Shutdown API client
            if self.api_client:
                await self.api_client.shutdown()

            # Close cache connections
            await self.cache.close()

            # Flush metrics
            self.metrics.flush()

            self.logger.info("All services shut down successfully")

        except Exception as e:
            self.logger.error("Error during shutdown", exception=e)

    async def run(self) -> None:
        """Run the MCP server."""
        try:
            # Initialize services
            await self.initialize()

            # Log startup metrics
            self.metrics.increment("server.start")
            self.metrics.gauge("server.environment", 1, tags={"env": self.config.environment.value})

            # Apply middleware
            if self.config.logging.log_request_duration:
                # Note: In a real implementation, you would apply this to your HTTP server
                self.logger.info("Request logging enabled")

            if self.config.metrics.enabled:
                # Note: In a real implementation, you would apply this to your HTTP server
                self.logger.info("Request metrics enabled")

            # Start MCP server
            self.logger.info("Starting MCP server")

            # Run with stdio transport
            async with stdio_server() as (read_stream, write_stream):
                await self.mcp_server.run(
                    read_stream,
                    write_stream,
                    self.mcp_server.create_initialization_options()
                )

        except Exception as e:
            self.logger.critical("Server failed", exception=e)
            raise
        finally:
            await self.shutdown()


async def main():
    """Main entry point."""
    # Set up basic logging before our structured logger is ready
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # Create and run server
    server = SemanticScholarMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
