<?xml version='1.0'?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:content="http://purl.org/rss/1.0/modules/content/"
xmlns:media="http://search.yahoo.com/mrss/">
<xsl:template match="//channel">
            <news>
                <xsl:apply-templates select="item">
                </xsl:apply-templates>
            </news>
        </xsl:template>
        <xsl:template match="item">
            <item>
                <title>
                    <xsl:value-of select="title"></xsl:value-of>
                </title>
                <link>
                    <xsl:value-of select="link"></xsl:value-of>
                </link>
                <media>
                    <xsl:value-of select="media:group/media:content[1]/@url"></xsl:value-of>
                </media>
            </item>
        </xsl:template>
</xsl:stylesheet>