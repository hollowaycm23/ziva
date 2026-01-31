"""
AniList Anime Knowledge Base Tool
Provides access to AniList's GraphQL API for anime information.
"""
import requests
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("AniListAnime")


class AniListClient:
    """
    Client for AniList GraphQL API.

    No authentication required for basic queries.
    Rate limit: 90 requests/minute.
    """

    def __init__(self):
        self.url = "https://graphql.anilist.co"
        self.session = requests.Session()

    def search_anime(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search for anime by title.

        Args:
            query: Anime title to search for
            limit: Maximum results to return (default: 5)

        Returns:
            List of anime information dictionaries
        """
        graphql_query = '''
        query ($search: String, $perPage: Int) {
          Page(page: 1, perPage: $perPage) {
            media(search: $search, type: ANIME, sort: POPULARITY_DESC) {
              id
              title {
                romaji
                english
                native
              }
              description
              episodes
              season
              seasonYear
              genres
              averageScore
              popularity
              format
              status
              coverImage {
                large
              }
              studios {
                nodes {
                  name
                }
              }
            }
          }
        }
        '''

        variables = {
            'search': query,
            'perPage': limit
        }

        try:
            response = self.session.post(
                self.url,
                json={'query': graphql_query, 'variables': variables},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if 'errors' in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []

            media = data.get('data', {}).get('Page', {}).get('media', [])
            return self._format_results(media)

        except Exception as e:
            logger.exception(f"Error searching AniList: {e}")
            return []

    def get_anime_by_id(self, anime_id: int) -> Optional[Dict]:
        """
        Get detailed information about a specific anime.

        Args:
            anime_id: AniList anime ID

        Returns:
            Anime information dictionary or None
        """
        graphql_query = '''
        query ($id: Int) {
          Media(id: $id, type: ANIME) {
            id
            title {
              romaji
              english
              native
            }
            description
            episodes
            season
            seasonYear
            genres
            averageScore
            popularity
            format
            status
            startDate { year month day }
            endDate { year month day }
            coverImage { large }
            bannerImage
            studios {
              nodes {
                name
                isAnimationStudio
              }
            }
            characters(sort: ROLE, perPage: 5) {
              nodes {
                name {
                  full
                }
              }
            }
            relations {
              edges {
                relationType
                node {
                  title { romaji }
                }
              }
            }
          }
        }
        '''

        try:
            response = self.session.post(
                self.url,
                json={'query': graphql_query, 'variables': {'id': anime_id}},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if 'errors' in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return None

            media = data.get('data', {}).get('Media')
            if media:
                return self._format_single_result(media)
            return None

        except Exception as e:
            logger.exception(f"Error fetching anime {anime_id}: {e}")
            return None

    def _format_results(self, media_list: List[Dict]) -> List[Dict]:
        """Format search results for readability."""
        results = []
        for media in media_list:
            results.append(self._format_single_result(media))
        return results

    def _format_single_result(self, media: Dict) -> Dict:
        """Format a single anime result."""
        # Clean HTML from description
        description = media.get('description', '')
        if description:
            import re
            description = re.sub(
                '<[^<]+?>', '', description)  # Strip HTML tags
            description = description[:500]  # Limit length

        # Get primary title (prefer English, fallback to Romaji)
        title = media.get('title', {})
        primary_title = title.get('english') or title.get(
            'romaji') or title.get('native', 'Unknown')

        # Get studio names
        studios = media.get('studios', {}).get('nodes', [])
        studio_names = [
            s.get('name') for s in studios if s.get(
                'isAnimationStudio', True)]

        return {
            'id': media.get('id'),
            'title': primary_title,
            'title_romaji': title.get('romaji'),
            'title_japanese': title.get('native'),
            'description': description,
            'episodes': media.get('episodes'),
            'season': media.get('season'),
            'year': media.get('seasonYear'),
            'genres': media.get('genres', []),
            'score': media.get('averageScore'),
            'popularity': media.get('popularity'),
            'format': media.get('format'),
            'status': media.get('status'),
            'studios': studio_names,
            'cover_image': media.get('coverImage', {}).get('large'),
        }


# Global instance
_client = None


def get_anilist_client() -> AniListClient:
    """Get or create global AniList client instance."""
    global _client
    if _client is None:
        _client = AniListClient()
    return _client
